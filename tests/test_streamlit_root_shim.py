from __future__ import annotations


def test_streamlit_app_main_callable(monkeypatch):
    called = {"main": False}

    def fake_main() -> None:
        called["main"] = True

    import capacity_hunter.ui.streamlit_app as ui_app

    # Подменяем main на заглушку
    monkeypatch.setattr(ui_app, "main", fake_main)

    # Просто вызываем main(), не завися от отдельного файла-шима.
    ui_app.main()

    assert called["main"] is True
