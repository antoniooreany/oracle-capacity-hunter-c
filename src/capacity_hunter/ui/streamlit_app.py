from __future__ import annotations

import logging

import streamlit as st

from capacity_hunter.config import load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier, format_capacity_summary


class StreamlitLogHandler(logging.Handler):
    """Log handler that writes finder logs into a Streamlit placeholder."""

    def __init__(self, placeholder: st.delta_generator.DeltaGenerator) -> None:  # type: ignore[name-defined]
        super().__init__()
        self.placeholder = placeholder

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        # Append to existing text; simplest is to overwrite with new content.
        existing = self.placeholder.text if hasattr(self.placeholder, "text") else ""
        new_text = f"{existing}\n{msg}" if existing else msg
        self.placeholder.text(new_text)


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

    # Load config (adapt to your real config model if needed)
    config = load_config()

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Search parameters")
        region = st.selectbox(
            "Region",
            options=config.regions,
            index=0,
        )
        shape = st.selectbox(
            "Shape",
            options=config.shapes,
            index=0,
        )
        max_price = st.slider(
            "Max hourly price",
            min_value=0.0,
            max_value=float(getattr(config, "max_price", 1.0) or 1.0),
            value=float(getattr(config, "max_price", 0.5) or 0.5),
            step=0.01,
        )

        run_forever = st.checkbox(
            "Run continuously (run_forever)", value=False
        )

        log_placeholder = st.empty()

        if st.button("Run hunter", type="primary"):
            with st.spinner("Running capacity hunter..."):
                notifier = TelegramNotifier(config=config)

                hunter = CapacityHunter(
                    config=config,
                    notifier=notifier,
                    region=region,
                    shape=shape,
                    max_price=max_price,
                    run_forever=run_forever,
                )

                finder_logger = logging.getLogger("capacity_hunter.finder")
                handler = StreamlitLogHandler(log_placeholder)
                handler.setLevel(logging.INFO)
                handler.setFormatter(logging.Formatter("%(message)s"))
                finder_logger.addHandler(handler)
                finder_logger.setLevel(logging.INFO)

                try:
                    result = (
                        hunter.run_forever()
                        if run_forever
                        else hunter.run_once()
                    )
                except Exception as exc:  # noqa: BLE001 - intentional catch-all to surface any hunter failure in the UI
                    st.error(f"Search failed: {exc}")
                    st.stop()
                finally:
                    finder_logger.removeHandler(handler)

            summary = format_capacity_summary(result)
            st.success("Capacity search completed.")
            st.markdown(summary)

    with col_right:
        st.subheader("Current config snapshot")
        if hasattr(config, "model_dump"):
            st.json(config.model_dump())
        else:
            st.json(config)


if __name__ == "__main__":
    main()