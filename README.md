# Oracle Cloud Capacity Hunter 🚀

Automates the annoying part of Oracle Cloud's Always Free tier: **Ampere A1 (ARM) instances are
frequently "Out of Capacity"** in popular regions. This tool loops across regions, availability
domains, and shapes, probing for free capacity via the official OCI Python SDK, and either just
notifies you (Telegram) or auto-launches the VM the moment a slot opens up.

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)]()

## Why this exists

Manually clicking "Create Instance" and refreshing until it works is tedious. This is a small but
complete DevOps automation: **Cloud API + retry logic + IaC-adjacent config + CI/CD + tests +
containerization** — the shape of a real infra tool, not a one-off script.

## Architecture

```
config.yaml (regions, shapes, credentials via env vars)
        │
        ▼
CapacityHunter.run_once() / run_forever()
        │
        ├─ for each region → IdentityClient.list_availability_domains()
        │       └─ for each AD → for each shape → ComputeClient.launch_instance()
        │              ├─ OutOfCapacity  → try next AD/shape/region
        │              ├─ mode=notify    → success → terminate probe instance → notify
        │              └─ mode=create    → success → wait RUNNING → fetch public IP → notify
        │
        ▼
TelegramNotifier.send()
```

Two ways to run it:
- **`--once`**: single pass, exit code reflects whether capacity was found. Designed for cron / a
  scheduled GitHub Actions workflow (no server needed to host it).
- **default (loop forever)**: exponential backoff (30s → 300s + jitter) until found. Designed to
  run as a long-lived Docker container.

## Project layout

```
oracle-capacity-hunter/
├── src/capacity_hunter/
│   ├── config.py      # loads + validates config.yaml, expands ${ENV_VARS}
│   ├── finder.py       # core hunting logic (OCI SDK calls, retry, backoff)
│   ├── notifier.py     # Telegram notifications (easy to extend: Slack, email, ...)
│   └── cli.py           # `capacity-hunter --config config.yaml [--once]`
├── tests/                # pytest, all OCI SDK calls mocked - no real cloud needed to test
├── Dockerfile
├── docker-compose.yml
├── config.example.yaml
├── requirements.txt / requirements-dev.txt / pyproject.toml
└── .github/workflows/
    ├── ci.yml                 # lint (ruff) + test (pytest) on every push/PR, 2 Python versions
    ├── docker-publish.yml     # build + push image to GHCR on push to main / tags
    └── scheduled-check.yml    # cron job: single-pass check every 15 min, no server required
```

## Language choice: why Python

- Oracle publishes an official, actively maintained Python SDK (`oci` on PyPI) with typed models
  for every resource — no hand-rolled REST calls or auth signing needed.
- Straightforward to unit test (mock the SDK clients) vs. shelling out to the `oci` CLI and
  parsing text/JSON output.
- Trivial to containerize and to reuse in a scheduled GitHub Actions job (same language as CI).

The earlier bash version (`wait-for-capacity.sh`, from the previous iteration of this project) still
works and needs zero setup beyond the `oci` CLI — keep it if you just want a quick one-off script.
This Python version is the "productionized" one: typed config, tests, CI/CD, Docker.

## Getting your `compartment_id` (and everything else OCI-related)

OCI's resource hierarchy: **Tenancy** (your account) → **Compartment** (like a folder/project) →
VMs, networks, storage live inside a compartment.

| Value | Where to find it |
|---|---|
| `compartment_id` | Console → ☰ Menu → Identity & Security → Compartments → open the root compartment (named after your tenancy) → copy its OCID. Or just use the **tenancy** OCID itself — using the root compartment is fine for a personal project. |
| `tenancy` OCID | Console → profile icon (top right) → "Tenancy: <name>" → OCID at the bottom |
| `user` OCID | Console → profile icon → "My profile" → OCID under your username |
| `fingerprint` + private key | Console → "My profile" → API Keys → "Add API Key" → "Generate API Key Pair" → download the `.pem`, note the fingerprint shown |
| `image_id` | `oci compute image list --compartment-id <id> --operating-system "Canonical Ubuntu" --operating-system-version "22.04" --shape "VM.Standard.A1.Flex"` |
| `subnet_id` | From your VCN/subnet — see the companion Terraform project (`network.tf`) if you set that up first, or Console → Networking → VCN → your subnet |

Or via CLI, once `oci setup config` is done:
```bash
oci iam compartment list --all
```

**Never commit these values.** `config.yaml` uses `${ENV_VAR}` placeholders precisely so secrets
stay out of git — see `config.example.yaml`.

## Quickstart

```bash
git clone <this-repo>
cd oracle-capacity-hunter
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

oci setup config   # one-time OCI CLI auth setup, if not already done

cp config.example.yaml config.yaml
export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx
export OCI_IMAGE_ID=ocid1.image.oc1..xxx
export OCI_SUBNET_ID=ocid1.subnet.oc1..xxx
export TELEGRAM_BOT_TOKEN=...   # optional
export TELEGRAM_CHAT_ID=...     # optional

capacity-hunter --config config.yaml --once   # single check
capacity-hunter --config config.yaml          # loop until found
```

## Running in Docker

```bash
docker compose up -d
docker compose logs -f
```

## Running via GitHub Actions (no server needed)

`scheduled-check.yml` runs a single-pass check every 15 minutes directly in Actions — no VM has to
sit around hosting this tool. Add these repo secrets: `OCI_CLI_USER`, `OCI_CLI_FINGERPRINT`,
`OCI_CLI_TENANCY`, `OCI_CLI_REGION`, `OCI_CLI_KEY_CONTENT` (the PEM contents), `OCI_COMPARTMENT_ID`,
`OCI_IMAGE_ID`, `OCI_SUBNET_ID`, `SSH_PUBLIC_KEY`, and optionally `TELEGRAM_BOT_TOKEN` /
`TELEGRAM_CHAT_ID`.

Set `mode: create` in config if you want it to actually launch on success; `mode: notify` (default)
just probes and terminates immediately so you don't burn your one free-tier slot on a bot's schedule
— you get pinged and launch manually (or flip to `create` and re-run).

## Testing

```bash
pytest                    # all OCI calls are mocked - runs anywhere, no cloud account needed
ruff check src tests      # lint
```

## Other automation ideas for this stack (Python + Cloud + Terraform + Kubernetes)

- **Full pipeline**: this hunter → Terraform (`terraform import` the found instance) → Ansible
  (install Docker/Java/Nginx) → GitHub Actions deploy on push — see the companion
  `oci-deploy/` Terraform project for the network + compute half of this.
- **Ansible playbook** for post-launch config management instead of cloud-init, if you want
  idempotent re-provisioning: `docker-install.yml`, `app-deploy.yml`.
- **Monitoring**: Prometheus + Node Exporter + Grafana dashboard on the same free-tier VM (CPU/RAM/
  disk/network), since you already have 24 GB RAM of headroom.
- **Multi-cloud fallback**: extend `finder.py` with a second backend (e.g. Fly.io or a different
  Oracle tenancy) so the hunter tries elsewhere if OCI stays out of capacity for too long.

## License

MIT — see `LICENSE`.

<!-- example feature branch marker -->
