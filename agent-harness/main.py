"""Main entrypoint for the Social Capital Launch-Pattern Agent Harness.

Orchestrates per-client ReAct investigations, pattern synthesis,
deterministic grounding validation, and report generation.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from clients import get_clients
from store import FindingsStore
from tools import SerperClient
from harness import Budget, LLMClient, run_client_investigation, run_synthesis
from validator import GroundingValidator, format_markdown_report

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("agent-harness")


def parse_args():
    parser = argparse.ArgumentParser(description="Social Capital Launch-Pattern Agent Harness")
    parser.add_argument(
        "--only-new",
        action="store_true",
        help="Skip investigation for clients already present in findings.json"
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
        help="Path to JSON findings cache (default: findings.json)"
    )
    return parser.parse_args()


def main():
    # Load environment variables from .env
    load_dotenv()

    args = parse_args()
    logger.info("=== Social Capital Launch-Pattern Agent Harness Initializing ===")
    if args.mock:
        logger.info("Mode: MOCK / DRY-RUN (no live API credits will be spent)")
    else:
        logger.info("Mode: LIVE API EXECUTION")
        # Validate API keys for live mode
        groq_key = os.getenv("GROQ_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        if not groq_key and not os.getenv("OPENAI_API_KEY"):
            logger.error("Error: GROQ_API_KEY (or OPENAI_API_KEY) is missing. Set it in .env or run with --mock.")
            sys.exit(1)
        if not serper_key:
            logger.error("Error: SERPER_API_KEY is missing. Set it in .env or run with --mock.")
            sys.exit(1)

    # Initialize store, budget, clients, and harness components
    store = FindingsStore(filepath=args.store)
    budget = Budget(max_tool_calls=args.budget)
    serper_client = SerperClient(mock=args.mock)
    llm_client = LLMClient(mock=args.mock)
    all_clients = get_clients()

    logger.info(f"Loaded {len(all_clients)} seed clients to investigate.")
    logger.info(f"Global tool-call budget: {budget.max_tool_calls}")

    # Step 1: Per-client investigation loop
    for idx, client in enumerate(all_clients, 1):
        client_name = client["name"]

        # Check skip-if-cached
        if args.only_new and store.has_client(client_name):
            logger.info(f"[{idx}/{len(all_clients)}] Skipping '{client_name}' (already in cache via --only-new)")
            continue

        logger.info(f"[{idx}/{len(all_clients)}] Investigating '{client_name}'...")
        client_finding = run_client_investigation(
            client=client,
            budget=budget,
            serper_client=serper_client,
            llm_client=llm_client,
            max_turns=12
        )

        # Save finding to cache immediately
        store.save_client_finding(client_name, client_finding)
        logger.info(
            f"Saved finding for '{client_name}': status={client_finding['status']}, "
            f"turns={client_finding['turns_taken']}, tools_used={len(client_finding['tool_results'])}"
        )

    # Step 2: Synthesis pass across all 9 clients
    all_stored_findings = store.get_all_findings()
    logger.info(f"Running synthesis pass across {len(all_stored_findings)} client findings...")
    synthesis_text = run_synthesis(all_stored_findings, llm_client)
    store.save_synthesis(synthesis_text, metadata={"tool_calls_total": budget.tool_calls_used})

    # Step 3: Grounding validation (deterministic, no LLM)
    logger.info("Executing deterministic grounding validation...")
    all_raw_tool_results = store.get_all_raw_tool_results()
    validator = GroundingValidator(all_raw_tool_results)
    synthesis_audit = validator.audit_text(synthesis_text)

    logger.info(
        f"Grounding Audit Complete: Score = {synthesis_audit['grounding_score_percent']}%, "
        f"Verified = {synthesis_audit['verified_count']}, "
        f"Unverified = {synthesis_audit['unverified_count']}"
    )

    # Step 4: Write report.md
    total_tools_in_findings = sum(len(c.get("tool_results", [])) for c in all_stored_findings.values())
    used_tools = budget.tool_calls_used if budget.tool_calls_used > 0 else total_tools_in_findings
    budget_stats = {
        "used": used_tools,
        "max": budget.max_tool_calls,
        "remaining": max(0, budget.max_tool_calls - used_tools)
    }
    markdown_report = format_markdown_report(synthesis_audit, all_stored_findings, budget_stats)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    logger.info(f"Successfully generated final report at '{args.output}'.")
    logger.info("=== Investigation and Grounding Complete ===")


if __name__ == "__main__":
    main()
