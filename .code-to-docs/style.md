# Documentation Style

- Use active voice and a pragmatic, technical tone
- Prefer short, dense paragraphs (2–4 sentences)
- Use dashes for bullet lists
- Keep headings in sentence case (no ALL CAPS)
- Avoid marketing language; focus on behavior, trade-offs, and failure cases

## Required sections for features

For any new feature, option, or behavior change, documentation MUST include:

- **Runtime**: how the tool runs (one-shot vs long-lived, backoff strategy, resource usage)
- **Exit codes**: explicit list of non-zero exit codes and what each one means
- **Failure semantics**: what counts as a “soft” failure vs “hard” failure (e.g., throttling vs invalid config), and how `--once` behaves in each case
- **Config keys**: all new/changed config fields, their defaults, and examples

## CLI and config documentation rules

- When describing CLI flags:
  - Always show a minimal example command line
  - Document interaction between flags (e.g., `--once` + `mode=notify`)
- When describing config:
  - Clearly differentiate **required** vs **optional** keys
  - Show one realistic YAML snippet, not a synthetic toy example
  - Mention environment variable expansion when relevant

## Error handling and logging

- Always document how errors are reported:
  - What is logged at INFO vs WARN vs ERROR
  - Which errors are retried, which abort the run
- For recoverable errors (capacity, throttling, network blips), describe:
  - How many retries are attempted
  - What backoff strategy is used
- For unrecoverable errors (bad credentials, invalid config, missing compartment/image/subnet), state:
  - That the run terminates
  - Which exit code is used

## Style for examples

- Prefer complete, copy-pastable examples over fragments
- Use a single canonical region/shape/compartment across examples for consistency
- For multi-step workflows (GitHub Actions, Docker, cron):
  - Show the full pipeline (config, CLI invocation, expected outcome)
  - Note any prerequisites (OCI CLI setup, secrets, API keys)

## Consistency with code

- Whenever behavior changes (runtime, exit codes, backoff, notification logic):
  - Update both README and any config/CLI reference sections
- If docs and code ever disagree, **code behavior wins**, and docs should be corrected to match it
- Prefer describing what the code actually does today, not future plans or TODOs
