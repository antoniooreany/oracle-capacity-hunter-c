from __future__ import annotations

from capacity_hunter.code_to_docs import build_payload


def test_build_payload_contract_shape() -> None:
    payload = build_payload("owner", "repo", 42)

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"title", "body_md", "labels"}

    assert isinstance(payload["title"], str)
    assert payload["title"].strip() != ""

    assert isinstance(payload["body_md"], str)
    assert payload["body_md"].strip() != ""

    assert isinstance(payload["labels"], list)
    assert all(isinstance(label, str) for label in payload["labels"])


def test_build_payload_markdown_sections_present() -> None:
    payload = build_payload("owner", "repo", 42)
    body = payload["body_md"]

    # Required section headers
    required = [
        "## Summary",
        "## Changes",
        "## Risks",
        "## Config",
        "## Testing",
    ]

    for header in required:
        assert header in body, f"Missing section header: {header}"


def test_build_payload_labels_nonempty() -> None:
    payload = build_payload("owner", "repo", 42)
    labels = payload["labels"]

    assert labels, "labels must not be empty"
    assert any(label.startswith("type:") for label in labels)
    assert any(label.startswith("area:") for label in labels)


def test_build_payload_title_and_labels_consistent_prefix() -> None:
    payload = build_payload("owner", "repo", 42)
    title = payload["title"]
    labels = payload["labels"]

    # Find type:* label, if any
    type_labels = [l for l in labels if l.startswith("type:")]
    if not type_labels:
        # If there is no type label, nothing to assert here
        return

    type_label = type_labels[0]
    type_suffix = type_label.split(":", 1)[1]

    # Title should start with the same suffix (e.g., "docs:", "ci:", "test:", "feat:", "chore:")
    # and must not mutate "feat" into "docs" or similar.
    assert title.lower().startswith(f"{type_suffix.lower()}:")
    assert "feat: update pr" not in title.lower() or "docs:" not in title.lower()


def test_build_payload_pr_number_in_title_and_body() -> None:
    pr_number = 99
    payload = build_payload("owner", "repo", pr_number)

    assert str(pr_number) in payload["title"]
    assert str(pr_number) in payload["body_md"]
