from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypedDict


class Payload(TypedDict):
    title: str
    body_md: str
    labels: list[str]


@dataclass
class ChangedFile:
    filename: str


def _github_request(url: str, token: str) -> dict:
    """Perform a GitHub API GET request and return JSON."""
    if not token:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN must be set in environment.")

    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:  # pragma: no cover - network errors
        raise SystemExit(f"GitHub API error {exc.code} for {url}: {exc.reason}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - network errors
        raise SystemExit(f"GitHub API connection error for {url}: {exc.reason}") from exc

    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise SystemExit(f"GitHub API returned invalid JSON for {url}: {exc}") from exc


def _list_changed_files(owner: str, repo: str, pr_number: int, token: str) -> list[ChangedFile]:
    """List changed files in a pull request via REST API."""
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    files: list[ChangedFile] = []
    page = 1

    while True:
        url = f"{base_url}?page={page}&per_page=100"
        data = _github_request(url, token)

        if not isinstance(data, list):
            break
        if not data:
            break

        for item in data:
            filename = item.get("filename", "")
            if filename:
                files.append(ChangedFile(filename=filename))

        if len(data) < 100:
            break
        page += 1

    return files


def _infer_type_label(filenames: Iterable[str]) -> str:
    """Infer a single type:* label from changed paths."""
    paths = list(filenames)

    if any(p.startswith(".github/workflows/") for p in paths):
        return "type:ci"
    if any(p.startswith("docs/") or p.endswith(".md") for p in paths):
        return "type:docs"
    if any(p.startswith("tests/") for p in paths):
        return "type:test"
    if any(p.startswith("src/capacity_hunter/") for p in paths):
        return "type:feat"

    return "type:chore"


def _infer_area_labels(filenames: Iterable[str]) -> list[str]:
    """Infer one or more area:* labels from changed paths."""
    areas: set[str] = set()
    for path in filenames:
        if path.startswith(".github/workflows/"):
            areas.add("area:ci")
        if path.startswith("docs/") or path.endswith(".md"):
            areas.add("area:docs")
        if path.startswith("tests/"):
            areas.add("area:tests")
        if path.startswith("src/capacity_hunter/"):
            areas.add("area:core")
    if not areas:
        areas.add("area:misc")
    return sorted(areas)


def build_payload(owner: str, repo: str, pr_number: int) -> Payload:
    """Build a documentation payload for a pull request."""
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GH_TOKEN must be set in environment.")

    files = _list_changed_files(owner, repo, pr_number, token)
    filenames = [f.filename for f in files]

    type_label = _infer_type_label(filenames)
    area_labels = _infer_area_labels(filenames)

    title_suffix = type_label.split(":", 1)[1]
    title = f"{title_suffix}: update PR #{pr_number} docs".replace("feat", "docs")

    summary_lines = [
        "## Summary",
        f"Generate documentation payload for `{owner}/{repo}#{pr_number}` based on the files changed in this pull request.",
        "",
    ]

    changes_lines = ["## Changes"]
    if filenames:
        for name in filenames:
            changes_lines.append(f"- {name}")
    else:
        changes_lines.append("- No files detected in this pull request (API result was empty).")
    changes_lines.append("")

    risks_lines = [
        "## Risks",
        "- Low: automation only updates PR metadata (title, body, labels).",
        "- No application runtime behavior is changed by the docs-assistant workflow itself.",
        "",
    ]

    config_lines = [
        "## Config",
        "- Requires `GITHUB_TOKEN` or `GH_TOKEN` in the environment.",
        "- Relies on GitHub REST API (`pulls/{pr_number}/files`) for the list of changed files.",
        "",
    ]

    testing_lines = [
        "## Testing",
        "- Verified `build_payload` contract with unit tests.",
        "- Workflow should be exercised on a test PR using a `[review-pr]` comment trigger.",
        "",
    ]

    body_md = "\n".join(summary_lines + changes_lines + risks_lines + config_lines + testing_lines)
    labels = [type_label, *area_labels]

    return {"title": title, "body_md": body_md, "labels": labels}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate PR docs payload.")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    payload = build_payload(args.owner, args.repo, args.pr)
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
