from __future__ import annotations

from unittest.mock import patch

import pytest

from capacity_hunter.code_to_docs import ChangedFile, build_payload


@pytest.fixture(autouse=True)
def _fake_github_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure build_payload sees a token without hitting the real network."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token-for-tests")


@pytest.fixture
def mock_changed_files():
    fake_files = [
        ChangedFile(filename="src/capacity_hunter/ui/streamlit_app.py"),
        ChangedFile(filename="tests/test_streamlit_root_shim.py"),
        ChangedFile(filename="docs/README.md"),
    ]
    with patch(
        "capacity_hunter.code_to_docs._list_changed_files",
        return_value=fake_files,
    ) as mocked:
        yield mocked


def test_build_payload_contract_shape(mock_changed_files) -> None:
    payload = build_payload("owner", "repo", 42)

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"title", "body_md", "labels"}

    assert isinstance(payload["title"], str)
    assert payload["title"].strip() != ""

    assert isinstance(payload["body_md"], str)
    assert payload["body_md"].strip() != ""

    assert isinstance(payload["labels"], list)
    assert all(isinstance(label, str) for label in payload["labels"])


def test_build_payload_markdown_sections_present(mock_changed_files) -> None:
    payload = build_payload("owner", "repo", 42)
    body = payload["body_md"]

    required = [
        "## Summary",
        "## Changes",
        "## Risks",
        "## Config",
        "## Testing",
    ]

    for header in required:
        assert header in body, f"Missing section header: {header}"


def test_build_payload_labels_nonempty(mock_changed_files) -> None:
    payload = build_payload("owner", "repo", 42)
    labels = payload["labels"]

    assert labels, "labels must not be empty"
    assert any(label.startswith("type:") for label in labels)
    assert any(label.startswith("area:") for label in labels)


def test_build_payload_title_and_labels_consistent_prefix(mock_changed_files) -> None:
    payload = build_payload("owner", "repo", 42)
    title = payload["title"]
    labels = payload["labels"]

    type_labels = [label for label in labels if label.startswith("type:")]
    if not type_labels:
        return

    type_label = type_labels[0]
    type_suffix = type_label.split(":", 1)[1]

    assert title.lower().startswith(f"{type_suffix.lower()}:")
    assert "feat: update pr" not in title.lower() or "docs:" not in title.lower()


def test_build_payload_pr_number_in_title_and_body(mock_changed_files) -> None:
    pr_number = 99
    payload = build_payload("owner", "repo", pr_number)

    assert str(pr_number) in payload["title"]
    assert str(pr_number) in payload["body_md"]


def test_build_payload_raises_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    with pytest.raises(SystemExit, match="GITHUB_TOKEN or GH_TOKEN"):
        build_payload("owner", "repo", 1)
