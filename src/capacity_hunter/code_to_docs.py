from __future__ import annotations

import json
from typing import TypedDict


class Payload(TypedDict):
    title: str
    body_md: str
    labels: list[str]


def build_payload(owner: str, repo: str, pr_number: int) -> Payload:
    title = f"docs: update PR #{pr_number} docs"

    body_md = "\n".join(
        [
            "## Summary",
            f"Generate documentation payload for `{owner}/{repo}#{pr_number}`.",
            "",
            "## Changes",
            f"- Adds a payload for {owner}/{repo}#{pr_number}.",
            "",
            "## Risks",
            "- Low risk: payload generation only updates PR metadata.",
            "",
            "## Config",
            "- No configuration changes in this iteration.",
            "",
            "## Testing",
            "- Unit tests cover the payload shape and required sections.",
        ]
    )

    labels = ["type:docs", "area:docs"]

    return {"title": title, "body_md": body_md, "labels": labels}


def main() -> None:
    payload = build_payload("owner", "repo", 0)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
