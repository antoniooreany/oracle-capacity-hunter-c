from __future__ import annotations

from pathlib import Path

from capacity_hunter.ui import launcher


def test_launcher_runs_streamlit_app(monkeypatch):
    called = {}

    def fake_call(cmd):
        called["cmd"] = cmd
        return 0

    monkeypatch.setattr(launcher.subprocess, "call", fake_call)

    rc = launcher.main()

    assert rc == 0
    assert called["cmd"][0]
    assert called["cmd"][1:4] == ["-m", "streamlit", "run"]
    assert Path(called["cmd"][4]).name == "streamlit_app.py"
