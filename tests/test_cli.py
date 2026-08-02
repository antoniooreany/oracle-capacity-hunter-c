from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from capacity_hunter.cli import main


def test_cli_once_found_calls_announce(monkeypatch):
    hunter = MagicMock()
    hunter.run_once.return_value = MagicMock(found=True)

    fake_config = SimpleNamespace(telegram=None)

    monkeypatch.setattr("capacity_hunter.cli.load_config", lambda path: fake_config)
    monkeypatch.setattr("capacity_hunter.cli.TelegramNotifier", lambda cfg: MagicMock())
    monkeypatch.setattr("capacity_hunter.cli.CapacityHunter", lambda config, notifier: hunter)

    rc = main(["--config", "config.yaml", "--once"])

    assert rc == 0
    hunter.run_once.assert_called_once()
    hunter._announce.assert_called_once_with(hunter.run_once.return_value)


def test_cli_once_not_found_returns_zero(monkeypatch):
    hunter = MagicMock()
    hunter.run_once.return_value = MagicMock(found=False)

    fake_config = SimpleNamespace(telegram=None)

    monkeypatch.setattr("capacity_hunter.cli.load_config", lambda path: fake_config)
    monkeypatch.setattr("capacity_hunter.cli.TelegramNotifier", lambda cfg: MagicMock())
    monkeypatch.setattr("capacity_hunter.cli.CapacityHunter", lambda config, notifier: hunter)

    rc = main(["--config", "config.yaml", "--once"])

    assert rc == 0
    hunter.run_once.assert_called_once()
    hunter._announce.assert_not_called()
