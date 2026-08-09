# Implementation Plan — oracle-capacity-hunter-claude

## 1. Goal & Scope

- Purpose: Monitor Oracle Cloud ARM Always Free instances and notify via Telegram when capacity is available.
- Scope v1.0:
  - Single-region monitoring (e.g. eu-frankfurt-1).
  - Single Telegram chat (your personal chat).
  - No auto-provisioning, только уведомления.

## 2. Architecture

Modules:

- `config.py` — load configuration (OCI tenancy/compartment OCIDs, region, Telegram token/chat_id) from environment/.env.
- `finder.py` — query Oracle Cloud API for ARM capacity (Compute and/or other services).
- `notifier.py` — send notifications to Telegram.
- `cli.py` — CLI entry point; orchestrates finder/notifier, error handling.

Flows:

1. `cli.py` → `config.py` → load config.
2. `cli.py` → `finder.py` → check capacity.
3. If capacity found → `notifier.py` → send Telegram message.
4. Log results (stdout/logfile).

## 3. Security & Secrets (OCI, Telegram)

- OCI:
  - Read `OCI_CONFIG_FILE` or env variables (`OCI_TENANCY_OCID`, `OCI_USER_OCID`, `OCI_KEY_FILE`, etc.).
  - Never commit keys or key files to Git.
- Telegram:
  - Read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from env or `.env` (gitignored).
  - Use `python-telegram-bot` (или другой выбранный фреймворк) с минимальным набором прав.

## 4. Tasks (SDD-aligned)

T001 — Create basic package skeleton (`config.py`, `finder.py`, `notifier.py`, `cli.py`).
T002 — Implement config loading (env/.env, validations).
T003 — Implement Oracle finder (single region, simple query, error handling).
T004 — Implement Telegram notifier (send message, basic formatting).
T005 — Implement CLI orchestration (arguments, logging, exit codes).
T006 — Tests for each module (unit tests, mocking Oracle/Telegram).
T007 — Add documentation (`README.md` + SDD spec).
T008 — Optional: scheduling integration (cron, Task Scheduler, etc.).

## 5. User Review Required

- Confirm Telegram framework choice (e.g. `python-telegram-bot` vs `aiogram`).
- Confirm regions and capacity types to monitor.
- Confirm acceptable polling interval and rate limits.

## 6. Open Questions

- Should the bot support multiple chats?
- Should results be persisted (e.g. sqlite) or just logged?
- Do we need HTTP proxy/timeout settings for Oracle/Telegram?
