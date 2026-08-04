from __future__ import annotations

import argparse
import json


def build_payload(owner: str, repo: str, pr: int) -> dict[str, object]:
    return {
        "title": "feat: add code-to-docs core skeleton",
        "body_md": (
            "## Summary\n"
            "This PR adds the initial code-to-docs core skeleton.\n\n"
            "## Changes\n"
            "- Added a contract document for the code-to-docs helper.\n"
            "- Added a CLI stub that emits a JSON PR description payload.\n"
            "- Added a test module for the initial contract.\n\n"
            "## Risks\n"
            "- No runtime behavior is changed.\n"
            "- The current implementation is a stub and will need follow-up work.\n\n"
            "## Config\n"
            "- No OCI, CLI, or deployment config changes.\n\n"
            "## Testing\n"
            "- pytest\n"
        ),
        "labels": ["type:feat", "area:docs"],
        "meta": {
            "owner": owner,
            "repo": repo,
            "pr": pr,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate PR documentation payload.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args.owner, args.repo, args.pr)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
