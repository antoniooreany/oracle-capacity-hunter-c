"""Notification backends. Currently just Telegram; easy to add Slack/email."""
from __future__ import annotations

import logging
from typing import Any

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


def format_capacity_summary(result: Any) -> str:
    """Return a human-friendly summary for a capacity search result.

    Minimal implementation to support the Streamlit UI and tests.
    Adapt it to your real CapacityResult model if needed.
    """
    found = getattr(result, "found", False)

    if not found:
        return "No capacity found."

    region = getattr(result, "region", None)
    shape = getattr(result, "shape", None)
    price = getattr(result, "price", None)
    instance_id = getattr(result, "instance_id", None)

    parts = ["Capacity found"]

    if region:
        parts.append(f"in region {region}")
    if shape:
        parts.append(f"for shape {shape}")
    if price is not None:
        parts.append(f"at price {price}")
    if instance_id:
        parts.append(f"(instance_id={instance_id})")

    return " ".join(parts) or f"Capacity result: {result!r}"