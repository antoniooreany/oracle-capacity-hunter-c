from __future__ import annotations

import logging

import streamlit as st

from capacity_hunter.config import load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier, format_capacity_summary


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

        if st.button("Run hunter", type="primary"):
            with st.spinner("Running capacity hunter..."):
                # Configure notifier if needed; here TelegramNotifier is an example
                notifier = TelegramNotifier(config=config)

<<<<<<< HEAD
                hunter = CapacityHunter(
                    config=config,
                    notifier=notifier,
                    region=region,
                    shape=shape,
                    max_price=max_price,
                    run_forever=run_forever,
=======
            handler = StreamlitLogHandler(log_placeholder)
            finder_logger = logging.getLogger("capacity_hunter.finder")
            finder_logger.addHandler(handler)
            finder_logger.setLevel(logging.INFO)

            try:
                notifier = TelegramNotifier(config.telegram) if config.telegram else None
                hunter = CapacityHunter(config, notifier=notifier)
                result = hunter.run_forever() if run_forever else hunter.run_once()
            except Exception as exc:
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
>>>>>>> 1932285 (fix(ui): catch unhandled exceptions in run_once/run_forever, show via st.error)
                )

                # Capture finder logs into Streamlit text area
                finder_logger = logging.getLogger("capacity_hunter.finder")
                log_messages: list[str] = []

                class StreamlitHandler(logging.Handler):
                    def emit(self, record: logging.LogRecord) -> None:
                        log_messages.append(self.format(record))

                handler = StreamlitHandler()
                handler.setLevel(logging.INFO)
                handler.setFormatter(logging.Formatter("%(message)s"))
                finder_logger.addHandler(handler)

                try:
                    result = hunter.run_once()
                finally:
                    finder_logger.removeHandler(handler)

            summary = format_capacity_summary(result)
            st.success("Capacity search completed.")
            st.markdown(summary)

            if log_messages:
                st.subheader("Finder logs")
                st.text("\n".join(log_messages))

    with col_right:
        st.subheader("Current config snapshot")
        if hasattr(config, "model_dump"):
            st.json(config.model_dump())
        else:
            st.json(config)


if __name__ == "__main__":
    main()
<<<<<<< HEAD
    
=======


>>>>>>> 1932285 (fix(ui): catch unhandled exceptions in run_once/run_forever, show via st.error)
