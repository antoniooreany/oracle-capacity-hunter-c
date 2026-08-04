"""Streamlit UI for capacity-hunter.

Run with:
    streamlit run streamlit_app.py

Lets you pick regions/shapes/mode by hand instead of editing config.yaml,
trigger a single check or a background loop, and watch live logs.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import streamlit as st

from capacity_hunter.config import (
    HunterConfig,
    InstanceConfig,
    ShapeConfig,
    TelegramConfig,
)
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier

COMMON_REGIONS = [
    "eu-frankfurt-1",
    "eu-amsterdam-1",
    "eu-milan-1",
    "eu-madrid-1",
    "eu-marseille-1",
    "uk-london-1",
    "us-ashburn-1",
    "us-phoenix-1",
    "ap-tokyo-1",
    "ap-singapore-1",
]

st.set_page_config(page_title="Oracle Capacity Hunter", page_icon="🚀", layout="centered")


# ---------------------------------------------------------------------------
# Logging -> Streamlit: collect records into session_state, render as a code block
# ---------------------------------------------------------------------------
class StreamlitLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        st.session_state.setdefault("logs", [])
        st.session_state["logs"].append(self.format(record))
        st.session_state["logs"] = st.session_state["logs"][-200:]  # cap size


def _setup_logging() -> None:
    if st.session_state.get("_logging_ready"):
        return
    handler = StreamlitLogHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger("capacity_hunter")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    st.session_state["_logging_ready"] = True


_setup_logging()
st.session_state.setdefault("logs", [])
st.session_state.setdefault("worker_thread", None)
st.session_state.setdefault("stop_event", None)
st.session_state.setdefault("last_result", None)

st.title("🚀 Oracle Capacity Hunter")
st.caption("Ручной подбор параметров вместо редактирования config.yaml")

# ---------------------------------------------------------------------------
# Sidebar: credentials / connection settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("OCI-подключение")
    oci_config_file = st.text_input("Путь к oci config", value=os.path.expanduser("~/.oci/config"))
    oci_profile = st.text_input("Профиль", value="DEFAULT")
    compartment_id = st.text_input("Compartment OCID", placeholder="ocid1.compartment.oc1..xxx")

    st.divider()
    st.header("Параметры инстанса")
    image_id = st.text_input("Image OCID", placeholder="ocid1.image.oc1..xxx")
    subnet_id = st.text_input("Subnet OCID", placeholder="ocid1.subnet.oc1..xxx")
    ssh_key_path = st.text_input(
        "SSH public key", value=os.path.expanduser("~/.ssh/id_ed25519.pub")
    )
    display_name = st.text_input("Display name", value="winwin-backend-vm")

    st.divider()
    st.header("Telegram (опционально)")
    tg_token = st.text_input("Bot token", type="password")
    tg_chat_id = st.text_input("Chat ID")

# ---------------------------------------------------------------------------
# Main panel: regions, shapes, mode
# ---------------------------------------------------------------------------
st.subheader("Регионы")
regions = st.multiselect(
    "Где искать capacity (порядок = приоритет)",
    options=COMMON_REGIONS,
    default=["eu-frankfurt-1", "eu-amsterdam-1"],
)
custom_region = st.text_input("Добавить регион вручную (необязательно)", placeholder="eu-stockholm-1")
if custom_region:
    regions = regions + [custom_region]

st.subheader("Shapes для перебора")
st.caption("Каждая строка — вариант, который скрипт попробует запросить. Порядок важен.")

if "shape_rows" not in st.session_state:
    st.session_state["shape_rows"] = [
        {"ocpus": 4, "memory_in_gbs": 24},
        {"ocpus": 2, "memory_in_gbs": 12},
    ]

for i, row in enumerate(st.session_state["shape_rows"]):
    c1, c2, c3 = st.columns([2, 2, 1])
    row["ocpus"] = c1.number_input("OCPU", min_value=1, max_value=4, value=row["ocpus"], key=f"ocpu_{i}")
    row["memory_in_gbs"] = c2.number_input(
        "RAM, GB", min_value=1, max_value=24, value=row["memory_in_gbs"], key=f"mem_{i}"
    )
    if c3.button("✖", key=f"del_{i}"):
        st.session_state["shape_rows"].pop(i)
        st.rerun()

if st.button("+ добавить вариант shape"):
    st.session_state["shape_rows"].append({"ocpus": 2, "memory_in_gbs": 12})
    st.rerun()

st.subheader("Режим")
mode = st.radio(
    "Что делать при удаче",
    options=["notify", "create"],
    format_func=lambda m: (
        "Только уведомить (пробный инстанс сразу удаляется)" if m == "notify" else "Создать и оставить VM"
    ),
    horizontal=False,
)

st.divider()


def _build_config() -> HunterConfig:
    shapes = [
        ShapeConfig(name="VM.Standard.A1.Flex", ocpus=r["ocpus"], memory_in_gbs=r["memory_in_gbs"])
        for r in st.session_state["shape_rows"]
    ]
    return HunterConfig(
        compartment_id=compartment_id,
        oci_config_file=oci_config_file,
        oci_config_profile=oci_profile,
        regions=regions,
        shapes=shapes,
        instance=InstanceConfig(
            display_name=display_name,
            image_id=image_id,
            subnet_id=subnet_id,
            ssh_public_key_path=ssh_key_path,
        ),
        min_interval_seconds=30,
        max_interval_seconds=300,
        mode=mode,
        telegram=TelegramConfig(bot_token=tg_token or None, chat_id=tg_chat_id or None),
    )


def _validate() -> list[str]:
    errors = []
    if not compartment_id:
        errors.append("Не указан Compartment OCID")
    if not image_id:
        errors.append("Не указан Image OCID")
    if not subnet_id:
        errors.append("Не указан Subnet OCID")
    if not Path(ssh_key_path).expanduser().exists():
        errors.append(f"SSH-ключ не найден: {ssh_key_path}")
    if not Path(oci_config_file).expanduser().exists():
        errors.append(f"OCI config не найден: {oci_config_file}")
    if not regions:
        errors.append("Не выбрано ни одного региона")
    if not st.session_state["shape_rows"]:
        errors.append("Не задано ни одного shape")
    return errors


col_run, col_bg, col_stop = st.columns(3)
run_once_clicked = col_run.button("▶ Проверить сейчас", use_container_width=True)
run_bg_clicked = col_bg.button(
    "🔁 Запустить в фоне",
    use_container_width=True,
    disabled=st.session_state["worker_thread"] is not None,
)
stop_clicked = col_stop.button(
    "⏹ Остановить",
    use_container_width=True,
    disabled=st.session_state["worker_thread"] is None,
)

if run_once_clicked:
    errors = _validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        with st.spinner("Проверяю все регионы/AD/shapes..."):
            try:
                notifier = TelegramNotifier(TelegramConfig(tg_token, tg_chat_id))
                hunter = CapacityHunter(_build_config(), notifier=notifier)
                result = hunter.run_once()
                if result.found:
                    hunter._announce(result)  # noqa: SLF001 - reuse CLI's own summary formatting
                st.session_state["last_result"] = result
            except Exception as exc:  # noqa: BLE001 - surface any error to the UI
                st.error(f"Ошибка: {exc}")

if run_bg_clicked:
    errors = _validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        stop_event = threading.Event()
        config = _build_config()

        def _worker() -> None:
            hunter = CapacityHunter(config, notifier=TelegramNotifier(config.telegram))
            result = hunter.run_forever(stop_event=stop_event)
            st.session_state["last_result"] = result
            st.session_state["worker_thread"] = None

        thread = threading.Thread(target=_worker, daemon=True)
        st.session_state["stop_event"] = stop_event
        st.session_state["worker_thread"] = thread
        thread.start()
        st.rerun()

if stop_clicked and st.session_state["stop_event"]:
    st.session_state["stop_event"].set()
    st.info("Остановка запрошена — фон завершится в течение ~1 секунды.")

if st.session_state["worker_thread"] is not None:
    st.info("🔁 Фоновый поиск идёт... нажми «Обновить лог» ниже, чтобы увидеть прогресс.")

if st.session_state["last_result"] is not None:
    result = st.session_state["last_result"]
    if result.found:
        st.success(
            f"Найдено! Регион: {result.region}, AD: {result.availability_domain}, "
            f"IP: {result.public_ip or '— (probe terminated)'}"
        )
    else:
        st.warning("Capacity не найдена за этот проход.")

st.subheader("Лог")
if st.button("🔄 Обновить лог"):
    st.rerun()
st.code("\n".join(st.session_state["logs"][-50:]) or "Пока пусто — запусти проверку.", language="log")
