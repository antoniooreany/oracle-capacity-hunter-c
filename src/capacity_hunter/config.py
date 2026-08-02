"""Load and validate config.yaml, expanding ${ENV_VAR} references."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigError(Exception):
    """Raised when config.yaml is missing required fields or env vars."""


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in os.environ:
                raise ConfigError(f"Environment variable '{name}' is not set (required by config)")
            return os.environ[name]
        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


@dataclass
class ShapeConfig:
    name: str
    ocpus: int
    memory_in_gbs: int


@dataclass
class InstanceConfig:
    display_name: str
    image_id: str
    subnet_id: str
    ssh_public_key_path: str
    assign_public_ip: bool = True
    user_data_path: str | None = None


@dataclass
class TelegramConfig:
    bot_token: str | None = None
    chat_id: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


@dataclass
class HunterConfig:
    compartment_id: str
    oci_config_file: str
    oci_config_profile: str
    regions: list[str]
    shapes: list[ShapeConfig]
    instance: InstanceConfig
    min_interval_seconds: int
    max_interval_seconds: int
    mode: str  # "notify" or "create"
    telegram: TelegramConfig = field(default_factory=TelegramConfig)

    def __post_init__(self) -> None:
        if self.mode not in ("notify", "create"):
            raise ConfigError(f"mode must be 'notify' or 'create', got '{self.mode}'")
        if not self.regions:
            raise ConfigError("at least one region must be configured")
        if not self.shapes:
            raise ConfigError("at least one shape must be configured")


def load_config(path: str | Path) -> HunterConfig:
    raw_text = Path(path).read_text()
    raw = yaml.safe_load(raw_text)
    raw = _expand_env(raw)

    oci_section = raw.get("oci", {})
    instance_section = raw["instance"]
    polling = raw.get("polling", {})
    telegram_section = raw.get("notifications", {}).get("telegram", {})

    return HunterConfig(
        compartment_id=oci_section["compartment_id"],
        oci_config_file=os.path.expanduser(oci_section.get("config_file", "~/.oci/config")),
        oci_config_profile=oci_section.get("config_profile", "DEFAULT"),
        regions=raw["regions"],
        shapes=[ShapeConfig(**s) for s in raw["shapes"]],
        instance=InstanceConfig(
            display_name=instance_section["display_name"],
            image_id=instance_section["image_id"],
            subnet_id=instance_section["subnet_id"],
            ssh_public_key_path=os.path.expanduser(instance_section["ssh_public_key_path"]),
            assign_public_ip=instance_section.get("assign_public_ip", True),
            user_data_path=instance_section.get("user_data_path"),
        ),
        min_interval_seconds=int(polling.get("min_interval_seconds", 30)),
        max_interval_seconds=int(polling.get("max_interval_seconds", 300)),
        mode=raw.get("mode", "notify"),
        telegram=TelegramConfig(
            bot_token=telegram_section.get("bot_token"),
            chat_id=telegram_section.get("chat_id"),
        ),
    )

