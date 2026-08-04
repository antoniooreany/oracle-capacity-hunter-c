# Code-to-Docs Contract

This document defines the initial contract for the `code_to_docs.py` helper.

## Goal

Generate a machine-readable PR documentation payload from repository metadata and pull request context.

## Inputs

The script should accept CLI arguments:

- `--owner`: GitHub repository owner
- `--repo`: GitHub repository name
- `--pr`: Pull request number

## Output

The script must write a JSON object to stdout with the following shape:

```json
{
  "title": "feat: add code-to-docs core skeleton",
  "body_md": "## Summary`n...`n## Changes`n...`n## Risks`n...`n## Config`n...`n## Testing`n...",
  "labels": ["type:feat", "area:docs"]
}
```

## Output Rules

- `title` must be a short PR title in conventional style.
- `body_md` must be GitHub-flavored Markdown.
- `body_md` should contain these sections:
  - `## Summary`
  - `## Changes`
  - `## Risks`
  - `## Config`
  - `## Testing`
- `labels` must be a JSON array of strings.

## Initial Stub Behavior

The first implementation may return a static payload as long as it:
- validates required arguments,
- emits valid JSON,
- follows the required schema.

## Follow-up Work

Future iterations should:
- inspect changed files,
- infer `type:*` and `area:*` labels,
- build PR content from diffs and commit messages,
- integrate with GitHub Actions for automatic PR updates.
