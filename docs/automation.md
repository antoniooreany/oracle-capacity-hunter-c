# Docs Assistant Automation

## Trigger

This automation runs on `issue_comment` when a comment on a pull request contains:

```text
[review-pr]
```

The workflow must ignore regular issues and only continue when `github.event.issue.pull_request` is present.

## Scope

This workflow is responsible for:

- generating a PR documentation payload via `scripts/code_to_docs.py`,
- updating PR title and body,
- applying inferred labels.

This workflow is not responsible for modifying application code.

## Flow

1. Trigger on PR comment with `[review-pr]`.
2. Run `scripts/code_to_docs.py` with:
   - `--owner`
   - `--repo`
   - `--pr`
3. Save JSON payload to `payload.json`.
4. Validate required payload keys:
   - `title`
   - `body_md`
   - `labels`
5. Update the PR title/body.
6. Apply labels through the Issues API because pull requests use issue label endpoints.[web:319]

## Expected Payload

```json
{
  "title": "ci: add docs assistant workflow",
  "body_md": "## Summary\n...\n## Changes\n...\n## Risks\n...\n## Config\n...\n## Testing\n...",
  "labels": ["type:ci", "area:ci"]
}
```

## Notes

- Changed files should be fetched from the GitHub pull request files endpoint.[web:317]
- Label inference should be based on changed paths.
- The workflow should fail fast on malformed payload output.
