from __future__ import annotations

import json
from typing import TypedDict


class Payload(TypedDict):
    title: str
    body_md: str
    labels: list[str]


def build_payload(owner: str, repo: str, pr_number: int) -> Payload:
    """Return a stub payload that satisfies the current contract and tests."""

    title = "feat: add code-to-docs core skeleton"

    body_md = "\n".join(
        [
            "## Summary",
            "Introduce the initial code-to-docs helper stub.",
            "",
            "## Changes",
            f"- Adds a stub payload for {owner}/{repo}#{pr_number}.",
            "",
            "## Risks",
            "- Low risk: payload is static and does not alter core behavior.",
            "",
            "## Config",
            "- No configuration changes in this iteration.",
            "",
            "## Testing",
            "- Unit tests cover the payload shape and required sections.",
        ]
    )

    labels = ["type:feat", "area:docs"]

    return {"title": title, "body_md": body_md, "labels": labels}


def main() -> None:
    """CLI entry point that prints the payload as JSON to stdout."""
    payload = build_payload("owner", "repo", 0)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()