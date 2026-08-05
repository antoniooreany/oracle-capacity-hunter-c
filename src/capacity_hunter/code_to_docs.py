from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, cast

import json

Docs = Dict[str, Any]


def build_docs() -> Docs:
    """Собирает словарь с данными для документации из внутренних источников."""
    docs: Docs = {}

    # TODO: здесь у тебя своя логика наполнения docs.
    # Например:
    # docs["summary"] = "Oracle Capacity Hunter core and UI"
    # docs["modules"] = ["capacity_hunter.cli", "capacity_hunter.ui"]

    return docs


def load_docs_from_file(path: Path) -> Docs:
    """Загружает словарь документации из JSON/YAML файла.

    Тип json.load/json.loads для mypy — Any, поэтому мы явно приводим его к Docs,
    чтобы избежать ошибки 'Returning Any from function declared to return "dict[Any, Any]".
    """
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    return cast(Docs, data)
