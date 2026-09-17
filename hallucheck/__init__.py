"""Hallucheck: Autonomous agent harness and deterministic grounding auditor.

Provides reusable, importable investigation workflows with zero hallucination guarantee.
"""

import os
import sys
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from dotenv import load_dotenv

from clients import load_targets, get_clients
from store import FindingsStore
from tools import (
    SerperClient,
    TOOL_SCHEMAS,
    TOOL_IMPLEMENTATIONS,
    register_tool,
    bind_serper_client
)
from harness import (
    Budget,
    LLMClient,
    run_client_investigation,
    run_synthesis,
    build_investigate_prompt,
    build_synthesis_prompt,
    DEFAULT_INVESTIGATE_CONTEXT,
    DEFAULT_SYNTHESIS_CONTEXT
)
from validator import GroundingValidator, format_markdown_report

logger = logging.getLogger("hallucheck")


@dataclass
class InvestigationReport:
    """Structured report produced by an investigation run."""

    investigation_name: str
    context: str
    findings: Dict[str, Any]
    synthesis: str
    ledger: List[Dict[str, Any]]
    stats: Dict[str, Any]
    budget: Dict[str, int]
    dossier_audit: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Render the complete investigation report as Markdown."""
        return format_markdown_report(self.dossier_audit, self.findings, self.budget)

    def to_json(self, indent: int = 2) -> str:
        """Serialize findings, synthesis, stats, and audit ledger to JSON string."""
        data = {
            "investigation_name": self.investigation_name,
            "context": self.context,
            "stats": self.stats,
            "budget": self.budget,
            "synthesis": self.synthesis,
            "ledger": self.ledger,
            "findings": self.findings,
        }
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def save_markdown(self, filepath: str = "report.md") -> None:
        """Write the markdown report to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_markdown())

    def save_json(self, filepath: str = "findings.json") -> None:
        """Write the findings JSON to a file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())


def investigate(
    config_path: str = "configs/social_capital.json",
    provider: str = "groq",
    budget_max_calls: int = 60,
    mock: bool = False,
    only_new: bool = False,
    limit: Optional[int] = None,
    store_path: Optional[str] = "findings.json",
    output_report_path: Optional[str] = "report.md",
    serper_client: Optional[SerperClient] = None,
    llm_client: Optional[LLMClient] = None,
    custom_tools: Optional[List[Dict[str, Any]]] = None,
    custom_implementations: Optional[Dict[str, Callable]] = None,
) -> InvestigationReport:
    """Run an autonomous grounded investigation over targets in a config.

    Args:
        config_path: Path to JSON configuration file (e.g. configs/social_capital.json).
        provider: Primary LLM provider ("groq", "openai", etc.).
        budget_max_calls: Global maximum search/news tool calls for the run.
        mock: If True, runs offline simulation without billable API calls.
        only_new: If True, skips targets already present in store_path.
        limit: Optional maximum number of targets to investigate.
        store_path: Path to findings.json cache file (None to disable disk persistence).
        output_report_path: Path to write markdown report (None to skip file write).
        serper_client: Optional pre-configured SerperClient instance.
        llm_client: Optional pre-configured LLMClient instance.
        custom_tools: Optional list of additional OpenAI-format tool schemas.
        custom_implementations: Optional mapping of tool_name -> callable.

    Returns:
        InvestigationReport object with .findings, .synthesis, .ledger, .to_markdown(), .to_json().
    """
    # Load environment variables
    load_dotenv()

    # Load configuration
    config = load_targets(config_path)
    investigation_name = config.get("investigation_name", "Target Investigation")
    inv_context = config.get("context", DEFAULT_INVESTIGATE_CONTEXT)
    syn_context = config.get("synthesis_context", DEFAULT_SYNTHESIS_CONTEXT)
    targets = config.get("targets", [])

    if limit is not None:
        targets = targets[:limit]
        logger.info(f"Limiting investigation to first {limit} targets: {[t['name'] for t in targets]}")

    run_mode = "mock" if mock else "live"
    if not mock:
        groq_key = os.getenv("GROQ_API_KEY")
        serper_key = os.getenv("SERPER_API_KEY")
        if not groq_key and not os.getenv("OPENAI_API_KEY"):
            raise ValueError("GROQ_API_KEY (or OPENAI_API_KEY) must be set in environment or run with mock=True.")
        if not serper_key:
            raise ValueError("SERPER_API_KEY must be set in environment or run with mock=True.")

    # Initialize store
    store = FindingsStore(filepath=store_path) if store_path else FindingsStore(filepath=":memory:")
    if not only_new and store_path:
        store.clear_clients()

    store.set_mode(run_mode, {
        "provider": provider if not mock else "mock",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "investigation_name": investigation_name
    })

    # Initialize budget
    budget = Budget(max_tool_calls=budget_max_calls)
    if only_new:
        existing_tools_count = sum(len(c.get("tool_results", [])) for c in store.get_all_findings().values())
        budget.tool_calls_used = existing_tools_count
        logger.info(f"Initialized budget with {existing_tools_count} existing tool calls in cache.")

    # Setup clients
    if serper_client is None:
        serper_client = SerperClient(mock=mock)
    bind_serper_client(serper_client)

    if llm_client is None:
        llm_client = LLMClient(mock=mock)

    # Tool schemas and implementations
    effective_schemas = list(TOOL_SCHEMAS)
    effective_impls = dict(TOOL_IMPLEMENTATIONS)
    if custom_tools:
        effective_schemas.extend(custom_tools)
    if custom_implementations:
        effective_impls.update(custom_implementations)

    # Parameterized prompt templates
    investigate_prompt = build_investigate_prompt(inv_context)
    synthesis_prompt = build_synthesis_prompt(syn_context)

    logger.info(f"Starting investigation: '{investigation_name}' ({len(targets)} targets, budget={budget.max_tool_calls})")

    # Step 1: Per-target investigation loop
    targets_investigated = 0
    for idx, target in enumerate(targets, 1):
        target_name = target["name"]

        if only_new and store.has_client(target_name):
            logger.info(f"[{idx}/{len(targets)}] Skipping '{target_name}' (cached via only_new)")
            continue

        targets_investigated += 1
        logger.info(f"[{idx}/{len(targets)}] Investigating '{target_name}'...")
        target_finding = run_client_investigation(
            client=target,
            budget=budget,
            serper_client=serper_client,
            llm_client=llm_client,
            max_turns=4,
            investigate_prompt=investigate_prompt,
            tool_schemas=effective_schemas,
            tool_implementations=effective_impls
        )
        target_finding["mode"] = run_mode
        store.save_client_finding(target_name, target_finding)
        logger.info(
            f"Saved finding for '{target_name}': status={target_finding['status']}, "
            f"turns={target_finding['turns_taken']}, tools={len(target_finding['tool_results'])}"
        )

    # Step 2: Synthesis pass
    all_stored_findings = store.get_all_findings()
    existing_synthesis = store.get_synthesis()
    if only_new and targets_investigated == 0 and existing_synthesis and isinstance(existing_synthesis, dict) and existing_synthesis.get("text"):
        logger.info("Using cached cross-target synthesis (all targets cached via --only-new)...")
        synthesis_text = existing_synthesis["text"]
    else:
        logger.info(f"Running cross-target synthesis across {len(all_stored_findings)} target findings...")
        synthesis_text = run_synthesis(all_stored_findings, llm_client, synthesis_prompt=synthesis_prompt)
        store.save_synthesis(synthesis_text, metadata={
            "tool_calls_total": budget.tool_calls_used,
            "mode": run_mode,
            "investigation_name": investigation_name
        })

    # Step 3: Grounding validation (Synthesis + all per-target findings)
    logger.info("Executing deterministic grounding validation...")
    all_raw_tool_results = store.get_all_raw_tool_results()
    validator = GroundingValidator(all_raw_tool_results)
    dossier_audit = validator.audit_dossier(synthesis_text, all_stored_findings)

    # Record audit ledger into store
    all_claims = dossier_audit["verified_claims"] + dossier_audit["unverified_claims"]
    stats = {
        "grounding_score_percent": dossier_audit["overall_grounding_score_percent"],
        "verified_count": dossier_audit["verified_count"],
        "unverified_count": dossier_audit["unverified_count"],
        "total_claims": dossier_audit["total_claims"]
    }
    store.save_audit_ledger(all_claims, stats)

    # Step 4: Budget summary
    total_tools_in_findings = sum(len(c.get("tool_results", [])) for c in all_stored_findings.values())
    used_tools = budget.tool_calls_used if budget.tool_calls_used > 0 else total_tools_in_findings
    budget_stats = {
        "used": used_tools,
        "max": budget.max_tool_calls,
        "remaining": max(0, budget.max_tool_calls - used_tools)
    }

    # Step 5: Construct InvestigationReport
    report = InvestigationReport(
        investigation_name=investigation_name,
        context=inv_context,
        findings=all_stored_findings,
        synthesis=synthesis_text,
        ledger=all_claims,
        stats=stats,
        budget=budget_stats,
        dossier_audit=dossier_audit
    )

    if output_report_path:
        report.save_markdown(output_report_path)
        logger.info(f"Wrote markdown report to '{output_report_path}'.")

    return report


__all__ = [
    "investigate",
    "InvestigationReport",
    "load_targets",
    "get_clients",
    "Budget",
    "LLMClient",
    "SerperClient",
    "GroundingValidator",
    "FindingsStore",
    "register_tool",
    "TOOL_SCHEMAS",
    "TOOL_IMPLEMENTATIONS",
    "build_investigate_prompt",
    "build_synthesis_prompt"
]
