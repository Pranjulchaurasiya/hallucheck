"""Comprehensive unit and integration test suite for the Social Capital Launch-Pattern Agent Harness.

Tests:
1. Grounding validator correctly flags deliberately fabricated handles vs real verified ones.
2. Grounding validator validates dates, URLs, and grounding score calculation.
3. Budget guardrail caps execution and blocks further tool calls once exhausted.
4. Malformed tool-call JSON and missing parameters are handled gracefully without crashing.
5. FindingsStore caching and skip-if-cached (--only-new) logic.
6. End-to-end dry-run in mock mode generating report.md.
"""

import os
import json
import pytest
from tools import SerperClient, TOOL_SCHEMAS
from harness import Budget, LLMClient, execute_tool_call, run_client_investigation
from store import FindingsStore
from validator import GroundingValidator, format_markdown_report


@pytest.fixture
def sample_raw_tool_results():
    """Sample raw tool results representing real retrieved search/news data."""
    return [
        {
            "client": "PlayerZero",
            "tool": "web_search",
            "result": {
                "results": [
                    {
                        "title": "PlayerZero Launch: AI Debugging",
                        "link": "https://x.com/PlayerZeroApp/status/1900123456789012345",
                        "snippet": "We are excited to announce PlayerZero! Thanks to @sama and @packyM for the early support.",
                        "position": 1
                    }
                ]
            }
        },
        {
            "client": "Wispr Flow",
            "tool": "web_search",
            "result": {
                "results": [
                    {
                        "title": "Wispr Flow: Voice-First Dictation",
                        "link": "https://x.com/WisprFlow/status/1890123456789012345",
                        "snippet": "Wispr Flow is live on February 12, 2026! Co-announced by @swyx and @gregisenberg.",
                        "position": 1
                    }
                ]
            }
        },
        {
            "client": "PlayerZero",
            "tool": "news_search",
            "result": {
                "results": [
                    {
                        "title": "PlayerZero Emerges with AI-Driven Quality Platform",
                        "link": "https://techcrunch.com/2026/03/05/playerzero-launch",
                        "snippet": "PlayerZero announces official product launch in March 2026.",
                        "date": "2026-03-05",
                        "source": "TechCrunch"
                    }
                ]
            }
        }
    ]


def test_grounding_validator_fabricated_vs_verified(sample_raw_tool_results):
    """Verify that a deliberately fabricated handle is flagged [UNVERIFIED] while real ones pass."""
    validator = GroundingValidator(sample_raw_tool_results)

    # Real handle present in mock data (@swyx, @packyM)
    is_swyx_valid, swyx_msg = validator.verify_handle("@swyx")
    assert is_swyx_valid is True
    assert "Found handle @swyx" in swyx_msg

    is_packy_valid, packy_msg = validator.verify_handle("@packyM")
    assert is_packy_valid is True

    # Deliberately fabricated handle
    is_fake_valid, fake_msg = validator.verify_handle("@completely_fake_creator_99999")
    assert is_fake_valid is False
    assert "not found in any retrieved search or news results" in fake_msg

    # Test audit_text on mixed assertion paragraph
    text_to_audit = (
        "The campaign was co-promoted by verified creators @swyx and @packyM, "
        "along with fabricated influencer @completely_fake_creator_99999."
    )
    audit = validator.audit_text(text_to_audit)

    assert audit["verified_count"] == 2
    assert audit["unverified_count"] == 1
    # 2 out of 3 = 66.7%
    assert audit["grounding_score_percent"] == 66.7

    # Verify that the fabricated handle is tagged with [UNVERIFIED] in annotated text
    assert "@completely_fake_creator_99999 **[UNVERIFIED]**" in audit["annotated_text"]
    assert "@swyx **[UNVERIFIED]**" not in audit["annotated_text"]


def test_grounding_validator_urls_and_dates(sample_raw_tool_results):
    """Verify that real URLs and dates match evidence, while fabricated ones fail."""
    validator = GroundingValidator(sample_raw_tool_results)

    # Real URL from TechCrunch
    real_url = "https://techcrunch.com/2026/03/05/playerzero-launch"
    is_url_valid, _ = validator.verify_url(real_url)
    assert is_url_valid is True

    # Fabricated URL
    fake_url = "https://fakenews.com/hallucinated-story-2026"
    is_fake_url_valid, _ = validator.verify_url(fake_url)
    assert is_fake_url_valid is False

    # Real Date
    is_date_valid, _ = validator.verify_date("February 12, 2026")
    assert is_date_valid is True

    # Fabricated Date
    is_fake_date_valid, _ = validator.verify_date("January 1, 2019")
    assert is_fake_date_valid is False


def test_budget_capping_guardrail():
    """Verify that the shared Budget strictly caps tool calls and blocks execution when exhausted."""
    budget = Budget(max_tool_calls=3)

    assert budget.remaining == 3
    assert budget.can_consume() is True

    assert budget.consume() is True
    assert budget.consume() is True
    assert budget.consume() is True

    # 4th call must be blocked
    assert budget.can_consume() is False
    assert budget.consume() is False
    assert budget.is_exhausted() is True
    assert budget.remaining == 0


def test_malformed_tool_call_handling():
    """Verify that malformed tool call JSON or missing arguments return structured errors without crashing."""
    client = SerperClient(mock=True)

    # 1. Broken JSON syntax
    broken_json = '{"query": "PlayerZero", broken_syntax'
    res, err = execute_tool_call("web_search", broken_json, client)
    assert err is not None
    assert "Malformed JSON" in err
    assert "error" in res

    # 2. Missing required parameter 'query'
    missing_query_json = '{"num_results": 10}'
    res, err = execute_tool_call("web_search", missing_query_json, client)
    assert err is not None
    assert "Missing required parameter 'query'" in err

    # 3. Unknown tool
    valid_json = '{"query": "PlayerZero"}'
    res, err = execute_tool_call("unknown_tool_func", valid_json, client)
    assert err is not None
    assert "Unknown tool" in err

    # 4. Valid call succeeds
    res, err = execute_tool_call("web_search", valid_json, client)
    assert err is None
    assert "results" in res


def test_findings_store(tmp_path):
    """Verify cache storage, retrieval, and skip-if-cached logic."""
    cache_file = str(tmp_path / "test_findings.json")
    store = FindingsStore(filepath=cache_file)

    assert store.has_client("PlayerZero") is False

    sample_finding = {
        "client": "PlayerZero",
        "launch_month": "2026-03",
        "status": "completed",
        "turns_taken": 3,
        "summary": "PlayerZero launch summary with @sama and @packyM.",
        "tool_results": [
            {
                "tool": "web_search",
                "result": {"results": [{"snippet": "@sama supported launch"}]}
            }
        ]
    }

    store.save_client_finding("PlayerZero", sample_finding)

    # Check persistence
    assert store.has_client("PlayerZero") is True
    retrieved = store.get_client("PlayerZero")
    assert retrieved["summary"] == sample_finding["summary"]

    # Check raw tool results aggregation
    all_raw = store.get_all_raw_tool_results()
    assert len(all_raw) == 1
    assert all_raw[0]["_client"] == "PlayerZero"


def test_react_loop_mock_execution():
    """Verify single client ReAct investigation loop under mock conditions."""
    budget = Budget(max_tool_calls=10)
    serper = SerperClient(mock=True)
    llm = LLMClient(mock=True)

    client_info = {"name": "PlayerZero", "launch_month": "2026-03"}
    finding = run_client_investigation(
        client=client_info,
        budget=budget,
        serper_client=serper,
        llm_client=llm,
        max_turns=12
    )

    assert finding["client"] == "PlayerZero"
    assert finding["status"] == "completed"
    assert finding["turns_taken"] >= 1
    assert len(finding["tool_results"]) > 0
    assert budget.tool_calls_used > 0
    assert "Research Findings for PlayerZero" in finding["summary"]


def test_audit_dossier_catches_unverified_in_client_summaries():
    """Verify that handles mentioned in per-client summaries (like @sama) are checked and flagged if ungrounded."""
    # PlayerZero has @sama in evidence; Wispr Flow does not
    client_findings = {
        "PlayerZero": {
            "summary": "PlayerZero launched with @sama and @packyM.",
            "tool_results": [
                {"result": {"results": [{"snippet": "Great support from @sama and @packyM"}]}}
            ]
        },
        "Wispr Flow": {
            "summary": "Wispr Flow announced by @swyx and @sama.",
            "tool_results": [
                {"result": {"results": [{"snippet": "Wispr Flow announced by @swyx"}]}}
            ]
        }
    }
    all_tools = []
    for c in client_findings.values():
        all_tools.extend(c["tool_results"])

    validator = GroundingValidator(all_tools)
    dossier = validator.audit_dossier(synthesis_text="Synthesis mentions @swyx.", client_findings=client_findings)

    # In PlayerZero, @sama should be verified
    pz_audit = dossier["client_audits"]["PlayerZero"]
    pz_sama = next((c for c in pz_audit["verified_claims"] if c["claim"] == "@sama"), None)
    assert pz_sama is not None
    assert pz_sama["status"] == "verified"

    # In Wispr Flow, @sama must be UNVERIFIED and flagged
    wf_audit = dossier["client_audits"]["Wispr Flow"]
    wf_sama = next((c for c in wf_audit["unverified_claims"] if c["claim"] == "@sama"), None)
    assert wf_sama is not None
    assert wf_sama["status"] == "unverified"
    assert "not found in Wispr Flow tool results" in wf_sama["detail"]
    assert "@sama **[UNVERIFIED]**" in dossier["annotated_client_findings"]["Wispr Flow"]["annotated_summary"]


def test_config_loader_and_compatibility():
    """Verify JSON config loading and backward-compatible get_clients / CLIENTS."""
    from clients import load_targets, get_clients, CLIENTS

    sc_data = load_targets("configs/social_capital.json")
    assert sc_data["investigation_name"] == "Social Capital Inc. — Launch-Pattern Investigation"
    assert len(sc_data["targets"]) == 9
    assert sc_data["targets"][0]["name"] == "PlayerZero"

    comp_data = load_targets("configs/example_competitor_research.json")
    assert "Competitor" in comp_data["investigation_name"]
    assert len(comp_data["targets"]) == 5

    # Backwards compatibility
    default_clients = get_clients()
    assert len(default_clients) == 9
    assert len(CLIENTS) == 9
    assert CLIENTS[0]["name"] == "PlayerZero"


def test_prompt_template_parameterization():
    """Verify system prompts are parameterized and match hardcoded text for Social Capital."""
    from harness import (
        build_investigate_prompt,
        build_synthesis_prompt,
        INVESTIGATE_SYSTEM_PROMPT,
        SYNTHESIS_SYSTEM_PROMPT
    )
    from clients import load_targets

    # Default call matches module-level constants
    assert build_investigate_prompt() == INVESTIGATE_SYSTEM_PROMPT
    assert build_synthesis_prompt() == SYNTHESIS_SYSTEM_PROMPT

    # Social capital config context reproduces identical prompt text
    sc_cfg = load_targets("configs/social_capital.json")
    rendered_inv = build_investigate_prompt(sc_cfg["context"])
    assert rendered_inv == INVESTIGATE_SYSTEM_PROMPT

    # Custom context parameterization works
    custom_inv = build_investigate_prompt("how 5 competitors price their SaaS products")
    assert "how 5 competitors price their SaaS products" in custom_inv


def test_tool_plugin_pattern_without_editing_harness():
    """Verify that adding a tool only requires schema + implementation in tools.py without touching harness.py."""
    from tools import register_tool, TOOL_SCHEMAS, TOOL_IMPLEMENTATIONS
    from harness import execute_tool_call

    wiki_schema = {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Look up Wikipedia summary for a topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Article title"}
                },
                "required": ["query"]
            }
        }
    }

    def mock_wikipedia_search(query: str):
        return {"title": query, "summary": f"Wikipedia article content for {query}"}

    # Register tool dynamically
    register_tool(wiki_schema, mock_wikipedia_search)

    assert "wikipedia_search" in TOOL_IMPLEMENTATIONS
    assert any(s["function"]["name"] == "wikipedia_search" for s in TOOL_SCHEMAS)

    # Execute tool via harness.execute_tool_call without any harness.py modifications
    res, err = execute_tool_call("wikipedia_search", json.dumps({"query": "Artificial Intelligence"}))
    assert err is None
    assert res["title"] == "Artificial Intelligence"
    assert "Wikipedia article content" in res["summary"]


def test_investigate_library_api(tmp_path):
    """Verify hallucheck.investigate() importable API with report object."""
    from hallucheck import investigate, InvestigationReport

    mock_report_path = str(tmp_path / "test_report.md")
    mock_store_path = str(tmp_path / "test_findings.json")

    report = investigate(
        config_path="configs/example_competitor_research.json",
        mock=True,
        budget_max_calls=15,
        limit=2,
        store_path=mock_store_path,
        output_report_path=mock_report_path
    )

    assert isinstance(report, InvestigationReport)
    assert len(report.findings) == 2
    assert "Cursor" in report.findings
    assert "GitHub Copilot" in report.findings
    assert isinstance(report.synthesis, str) and len(report.synthesis) > 0
    assert isinstance(report.ledger, list)
    assert "grounding_score_percent" in report.stats

    # Verify report methods
    md = report.to_markdown()
    assert isinstance(md, str) and len(md) > 100
    assert os.path.exists(mock_report_path)

    js = report.to_json()
    assert isinstance(js, str)
    parsed = json.loads(js)
    assert parsed["investigation_name"] == report.investigation_name


