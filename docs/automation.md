# Docs Assistant Automation

## Trigger

Run on PR comment containing `[review-pr]`.

## Flow

1. Trigger on `issue_comment`.
2. Continue only if `github.event.issue.pull_request` exists.
3. Run `scripts/code_to_docs.py`.
4. Validate `title`, `body_md`, `labels`.
5. Update PR title/body.
6. Apply labels via Issues API.
