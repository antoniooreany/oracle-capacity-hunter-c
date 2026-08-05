from __future__ import annotations

import logging

import streamlit as st

from capacity_hunter.config import ConfigError, load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier


class StreamlitLogHandler(logging.Handler):
    """Logging handler that streams formatted records into a Streamlit placeholder."""

    def __init__(self, placeholder: st.delta_generator.DeltaGenerator) -> None:
        super().__init__()
        self._placeholder = placeholder
        self._lines: list[str] = []
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        self._lines.append(self.format(record))
        # Keep the last N lines so the box doesn't grow unbounded.
        tail = self._lines[-200:]
        self._placeholder.code("\n".join(tail), language="log")


def main() -> None:
    st.set_page_config(
        page_title="Oracle Capacity Hunter",
        page_icon="🧠",
        layout="wide",
    )

    st.title("Oracle Capacity Hunter UI")
    st.caption(
        "Streamlit UI over capacity_hunter core: config, finder, notifier."
    )

    config_path = st.sidebar.text_input("Config file path", value="config.yaml")

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        st.error(f"Failed to load config from '{config_path}': {exc}")
        st.stop()
    except FileNotFoundError:
        st.error(f"Config file not found: '{config_path}'")
        st.stop()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Search parameters")
        st.write("Regions:", ", ".join(config.regions))
        st.write("Shapes:", ", ".join(shape.name for shape in config.shapes))
        st.write("Mode:", config.mode)
        st.write(
            "Polling interval:",
            f"{config.min_interval_seconds}s – {config.max_interval_seconds}s",
        )

        run_forever = st.checkbox("Run continuously (run_forever)", value=False)

        if st.button("Run hunter", type="primary"):
            st.subheader("Live log")
            log_placeholder = st.empty()
            log_placeholder.code("Starting search...", language="log")

            handler = StreamlitLogHandler(log_placeholder)
            finder_logger = logging.getLogger("capacity_hunter.finder")
            finder_logger.addHandler(handler)
            finder_logger.setLevel(logging.INFO)

            try:
                notifier = TelegramNotifier(config.telegram) if config.telegram else None
                hunter = CapacityHunter(config, notifier=notifier)
                result = hunter.run_forever() if run_forever else hunter.run_once()
            except Exception as exc:  # noqa: BLE001 - intentional catch-all to surface any hunter failure in the UI  # noqa: BLE001 - intentional catch-all to surface any hunter failure in the UI
                st.error(f"Search failed: {exc}")
                st.stop()
            finally:
                finder_logger.removeHandler(handler)

            if result.found:
                st.success("Capacity found!")
                st.write(
                    {
                        "region": result.region,
                        "availability_domain": result.availability_domain,
                        "shape": result.shape.name if result.shape else None,
                        "public_ip": result.public_ip,
                        "instance_id": result.instance_id,
                    }
                )
            else:
                st.info("No capacity found this run.")

    with col_right:
        st.subheader("Current config snapshot")
        st.json(
            {
                "compartment_id": config.compartment_id,
                "regions": config.regions,
                "shapes": [s.name for s in config.shapes],
                "mode": config.mode,
                "min_interval_seconds": config.min_interval_seconds,
                "max_interval_seconds": config.max_interval_seconds,
            }
        )


if __name__ == "__main__":
    main()




