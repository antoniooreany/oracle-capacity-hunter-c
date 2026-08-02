"""CLI entrypoint: `python -m capacity_hunter.cli --config config.yaml [--once]`."""
from __future__ import annotations

import argparse
import logging
import sys

from capacity_hunter.config import ConfigError, load_config
from capacity_hunter.finder import CapacityHunter
from capacity_hunter.notifier import TelegramNotifier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hunt for free OCI Ampere A1 capacity.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Single pass and exit (good for cron / scheduled CI). Default: loop forever.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    hunter = CapacityHunter(config, notifier=TelegramNotifier(config.telegram))
    result = hunter.run_once() if args.once else hunter.run_forever()

    if args.once:
        if result.found:
            hunter._announce(result)
        else:
            logging.getLogger(__name__).info("No capacity found this pass.")

    return 0 if result.found or not args.once else 1


if __name__ == "__main__":
    raise SystemExit(main())

