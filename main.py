"""Main CLI entrypoint for Hallucheck.

Thin CLI wrapper delegating to the reusable hallucheck.investigate() package API.
"""

import sys
import argparse
import logging
from dotenv import load_dotenv

from hallucheck import investigate

# Configure clean UTF-8 logging
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("agent-harness")


def parse_args():
    parser = argparse.ArgumentParser(description="Hallucheck Autonomous Grounding Auditor CLI")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/social_capital.json",
        help="Path to investigation JSON config (default: configs/social_capital.json)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="groq",
        help="Primary LLM provider (default: groq)"
    )
    parser.add_argument(
        "--only-new",
        action="store_true",
        help="Skip investigation for targets already present in findings cache"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run harness in offline mock mode without making live API calls"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=60,
        help="Global maximum tool calls across the entire run (default: 60)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="report.md",
        help="Path to output markdown report (default: report.md)"
    )
    parser.add_argument(
        "--store",
        type=str,
        default="findings.json",
        help="Path to findings cache (default: findings.json)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of seed targets to investigate (e.g. 3)"
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    logger.info("=== Hallucheck Autonomous Grounding Auditor Initializing ===")
    logger.info(f"Config: {args.config}")
    logger.info(f"Mode: {'MOCK / DRY-RUN' if args.mock else 'LIVE API EXECUTION'}")

    try:
        report = investigate(
            config_path=args.config,
            provider=args.provider,
            budget_max_calls=args.budget,
            mock=args.mock,
            only_new=args.only_new,
            limit=args.limit,
            store_path=args.store,
            output_report_path=args.output,
        )
    except Exception as e:
        logger.error(f"Investigation execution failed: {e}")
        sys.exit(1)

    logger.info(
        f"Grounding Audit Complete: Overall Score = {report.stats['grounding_score_percent']}%, "
        f"Verified = {report.stats['verified_count']}, "
        f"Unverified = {report.stats['unverified_count']} (Total Claims Audited = {report.stats['total_claims']})"
    )
    logger.info(f"Successfully generated final report at '{args.output}'.")
    logger.info("=== Investigation and Grounding Complete ===")


if __name__ == "__main__":
    main()
