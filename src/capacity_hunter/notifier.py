"""Notification backends. Currently just Telegram; easy to add Slack/email."""
from __future__ import annotations

import logging

import requests

from capacity_hunter.config import TelegramConfig

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, config: TelegramConfig, timeout: float = 10.0) -> None:
        self._config = config
        self._timeout = timeout

    def send(self, message: str) -> bool:
        if not self._config.enabled:
            logger.debug("Telegram not configured, skipping notification: %s", message)
            return False
        url = f"https://api.telegram.org/bot{self._config.bot_token}/sendMessage"
        try:
            resp = requests.post(
                url,
                data={"chat_id": self._config.chat_id, "text": message},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException:
            logger.exception("Failed to send Telegram notification")
            return False
