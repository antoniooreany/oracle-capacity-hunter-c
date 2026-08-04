from __future__ import annotations

import streamlit as st

from capacity_hunter.config import load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import format_capacity_summary


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

    # Load config (you can adapt this to your real config model)
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
            max_value=float(config.max_price or 1.0),
            value=float(config.max_price or 0.5),
            step=0.01,
        )

      if st.button("Find capacity", type="primary"):
          with st.spinner("Searching for capacity..."):
              hunter = CapacityHunter(config=config, notifier=None)
              result = hunter.run_once()

          summary = format_capacity_summary(result)
          st.success("Capacity search completed.")
          st.markdown(summary)

    with col_right:
        st.subheader("Current config snapshot")
        st.json(config.model_dump() if hasattr(config, "model_dump") else config)


if __name__ == "__main__":
    main()
