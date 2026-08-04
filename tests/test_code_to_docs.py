from __future__ import annotations

from capacity_hunter.code_to_docs import build_payload


def test_build_payload_contains_required_keys() -> None:
    payload = build_payload("antoniooreany", "oracle-capacity-hunter-claude", 7)

    assert payload["title"]
    assert payload["body_md"]
    assert payload["labels"] == ["type:feat", "area:docs"]


def test_build_payload_body_has_required_sections() -> None:
    payload = build_payload("antoniooreany", "oracle-capacity-hunter-claude", 7)
    body = payload["body_md"]

    assert "## Summary" in body
    assert "## Changes" in body
    assert "## Risks" in body
    assert "## Config" in body
    assert "## Testing" in body
