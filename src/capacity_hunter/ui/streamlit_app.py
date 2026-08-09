from __future__ import annotations

import dataclasses
import html
import json
import logging
import time
from pathlib import Path

import streamlit as st

from capacity_hunter.config import load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier, format_capacity_summary

CUSTOM_CSS = """
<style>
.log-box {
    background: #0e1117;
    border: 1px solid #2b2f3a;
    border-radius: 8px;
    padding: 12px 14px;
    height: 260px;
    overflow-y: auto;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.82rem;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
    color: #c9d1d9;
}
.log-box:empty::before {
    content: "Логи появятся здесь после запуска.";
    color: #6e7681;
    font-style: italic;
}
.status-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-left: 8px;
}
.status-pill.watching {
    background: #3a2f10;
    color: #f0b429;
}
.status-pill.idle {
    background: #1f2630;
    color: #8b949e;
}
</style>
"""


class StreamlitLogHandler(logging.Handler):
    """Log handler that renders finder logs into a scrollable HTML box."""

    def __init__(self, placeholder) -> None:
        super().__init__()
        self.placeholder = placeholder
        self._lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self._lines.append(self.format(record))
        self._render()

    def _render(self) -> None:
        escaped = "\n".join(html.escape(line) for line in self._lines[-200:])
        self.placeholder.markdown(f"<div class='log-box'>{escaped}</div>", unsafe_allow_html=True)


def _run_once_with_logging(scoped_config, log_placeholder) -> object:
    notifier = TelegramNotifier(scoped_config.telegram)
    hunter = CapacityHunter(config=scoped_config, notifier=notifier)

    finder_logger = logging.getLogger("capacity_hunter.finder")
    handler = StreamlitLogHandler(log_placeholder)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))
    finder_logger.addHandler(handler)
    finder_logger.setLevel(logging.INFO)
    handler._render()

    try:
        return hunter.run_once()
    finally:
        finder_logger.removeHandler(handler)


def _mask_secret(value: str | None, keep_start: int = 4, keep_end: int = 4) -> str:
    if not value:
        return "—"
    if len(value) <= keep_start + keep_end:
        return "•" * len(value)
    return f"{value[:keep_start]}{'•' * 8}{value[-keep_end:]}"


def main() -> None:
    st.set_page_config(page_title="Oracle Capacity Hunter", page_icon="🧠", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("🧠 Oracle Capacity Hunter")
    st.caption("Streamlit UI over capacity_hunter core: config, finder, notifier.")

    config_path = Path(__file__).resolve().parents[3] / "config.yaml"
    config = load_config(config_path)

    if "watching" not in st.session_state:
        st.session_state.watching = False
    if "scoped_config" not in st.session_state:
        st.session_state.scoped_config = None
    if "sleep_seconds" not in st.session_state:
        st.session_state.sleep_seconds = config.min_interval_seconds

    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        with st.container(border=True):
            st.subheader("Search parameters")
            region = st.selectbox(
                "Region", options=config.regions, index=0,
                key="region_select", disabled=st.session_state.watching,
            )
            shape = st.selectbox(
                "Shape",
                options=config.shapes,
                index=0,
                format_func=lambda s: f"{s.name} ({s.ocpus} OCPU, {s.memory_in_gbs} GB)",
                key="shape_select",
                disabled=st.session_state.watching,
            )
            st.caption("💡 Max hourly price пока не используется движком поиска (нет OCPU/цены в OCI free tier логике).")
            run_forever = st.checkbox(
                "Continuous watch mode",
                value=False, key="run_forever_checkbox", disabled=st.session_state.watching,
                help="Автоматически повторяет поиск с растущей паузой, пока не найдёт capacity.",
            )

            pill_class = "watching" if st.session_state.watching else "idle"
            pill_text = f"⏳ watching, next check in {st.session_state.sleep_seconds}s" if st.session_state.watching else "idle"
            st.markdown(f"<span class='status-pill {pill_class}'>{pill_text}</span>", unsafe_allow_html=True)
            st.write("")

            if not st.session_state.watching:
                run_clicked = st.button("▶ Run hunter", type="primary", key="run_hunter_button")
            else:
                run_clicked = False
                if st.button("■ Stop watching", key="stop_watch_button"):
                    st.session_state.watching = False
                    st.rerun()

        st.write("")
        with st.container(border=True):
            st.subheader("Log")
            log_placeholder = st.empty()
            log_placeholder.markdown("<div class='log-box'></div>", unsafe_allow_html=True)
            result_placeholder = st.container()

        if run_clicked:
            scoped_config = dataclasses.replace(config, regions=[region], shapes=[shape])
            with st.spinner("Running capacity hunter..."):
                try:
                    result = _run_once_with_logging(scoped_config, log_placeholder)
                except Exception as exc:  # noqa: BLE001
                    result_placeholder.error(f"Search failed: {exc}")
                    st.stop()

            if result.found:
                result_placeholder.success("✅ " + format_capacity_summary(result))
            elif run_forever:
                st.session_state.watching = True
                st.session_state.scoped_config = scoped_config
                st.session_state.sleep_seconds = config.min_interval_seconds
                st.rerun()
            else:
                result_placeholder.warning("Capacity not found this pass.")

        elif st.session_state.watching:
            try:
                result = _run_once_with_logging(st.session_state.scoped_config, log_placeholder)
            except Exception as exc:  # noqa: BLE001
                st.session_state.watching = False
                result_placeholder.error(f"Search failed: {exc}")
                st.stop()

            if result.found:
                st.session_state.watching = False
                result_placeholder.success("✅ " + format_capacity_summary(result))
            else:
                sleep_for = st.session_state.sleep_seconds
                st.session_state.sleep_seconds = min(
                    sleep_for * 2, st.session_state.scoped_config.max_interval_seconds
                )
                time.sleep(sleep_for)
                st.rerun()

    with col_right:
        with st.container(border=True):
            st.subheader("Current config")
            st.metric("Region(s)", ", ".join(config.regions))
            st.metric("Shape(s)", ", ".join(s.name for s in config.shapes))
            st.metric("Mode", config.mode)

            with st.expander("Full config snapshot (JSON)"):
                show_secrets = st.checkbox("Показать секреты", value=False, key="show_secrets")
                data = config.model_dump() if hasattr(config, "model_dump") else dataclasses.asdict(config)
                if not show_secrets:
                    data = json.loads(json.dumps(data, default=str))
                    tg = data.get("telegram", {})
                    tg["bot_token"] = _mask_secret(tg.get("bot_token"))
                    tg["chat_id"] = _mask_secret(tg.get("chat_id"), keep_start=2, keep_end=2)
                st.code(json.dumps(data, indent=2, ensure_ascii=False, default=str), language="json")


if __name__ == "__main__":
    main()
