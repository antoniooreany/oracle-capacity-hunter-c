from __future__ import annotations

import runpy


def test_root_streamlit_app_calls_ui_main(monkeypatch):
    called = {"main": False}

    def fake_main():
        called["main"] = True

    import capacity_hunter.ui.streamlit_app as ui_app

    monkeypatch.setattr(ui_app, "main", fake_main)

    runpy.run_path("streamlit_app.py", run_name="__main__")

    assert called["main"] is True
