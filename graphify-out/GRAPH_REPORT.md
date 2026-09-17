# Graph Report - Hallucheck  (2026-09-17)

## Corpus Check
- 31 files · ~79,163 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 432 nodes · 640 edges · 30 communities (29 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Budget
- FindingsStore
- Budget
- GroundingValidator
- GroundingValidator
- FindingsStore
- SerperClient
- SerperClient
- Investigation Summary – Airwallex Launch (AgentOS & Related Products)
- app.js
- PRD.md — Product Requirements Document (Hallucheck)
- serve.py
- agent-harness/clients.py
- Investigation Summary – Airwallex Launch (AgentOS & Related Products)
- API.md — Interface Specifications & Contracts
- 2. Core Operational Principles for AI Agents
- 2. Component Pipeline & Data Flow
- TASKS.md — Project Roadmap & Task Ledger
- 2. Entity Definitions & Types
- Hallucheck — Autonomous Grounding Auditor & Investigation Package
- deploy/app.js
- test_harness.py
- agent-harness/main.py
- LLMClient
- __init__.py
- investigate
- InvestigationReport
- .save_json
- main.py
- sample_raw_tool_results

## God Nodes (most connected - your core abstractions)
1. `investigate()` - 26 edges
2. `FindingsStore` - 21 edges
3. `GroundingValidator` - 21 edges
4. `SerperClient` - 19 edges
5. `main()` - 16 edges
6. `SerperClient` - 16 edges
7. `GroundingValidator` - 16 edges
8. `FindingsStore` - 15 edges
9. `Budget` - 15 edges
10. `LLMClient` - 14 edges

## Surprising Connections (you probably didn't know these)
- `investigate()` --uses--> `Budget`  [INFERRED]
  hallucheck/__init__.py → agent-harness/harness.py
- `test_budget_capping_guardrail()` --uses--> `Budget`  [INFERRED]
  test_harness.py → agent-harness/harness.py
- `test_react_loop_mock_execution()` --uses--> `Budget`  [INFERRED]
  test_harness.py → agent-harness/harness.py
- `investigate()` --uses--> `LLMClient`  [INFERRED]
  hallucheck/__init__.py → agent-harness/harness.py
- `test_react_loop_mock_execution()` --uses--> `LLMClient`  [INFERRED]
  test_harness.py → agent-harness/harness.py

## Import Cycles
- None detected.

## Communities (30 total, 1 thin omitted)

### Community 0 - "Budget"
Cohesion: 0.13
Nodes (10): Budget, A single shared counter across the whole run (all clients + synthesis)., Check if any tool budget remains., Consume 1 unit of budget if available. Returns True if granted, False if…, Return whether the budget is fully spent., Remaining allowed tool calls., Verify that the shared Budget strictly caps tool calls and blocks execution…, Verify single client ReAct investigation loop under mock conditions. (+2 more)

### Community 1 - "FindingsStore"
Cohesion: 0.10
Nodes (17): FindingsStore, Any, Reset client findings, synthesis, and ledger for a fresh run., Return all client findings., Gather all raw tool results across all stored client runs., Manages flat JSON storage of client investigation findings and tool evidence., Load findings from disk if file exists., Persist findings to disk. (+9 more)

### Community 2 - "Budget"
Cohesion: 0.10
Nodes (19): Budget, execute_tool_call(), LLMClient, Any, ReAct loop, Budget management, and LLM provider abstraction. Supports Groq as…, Call LLM with Groq as primary, falling back to OpenAI only if Groq fails., Normalize response into a clean dictionary., Realistic mock behavior for test suite and dry-runs. (+11 more)

### Community 3 - "GroundingValidator"
Cohesion: 0.10
Nodes (19): Verify that real URLs and dates match evidence, while fabricated ones fail., Verify that handles mentioned in per-client summaries (like @sama) are checked…, Verify that a deliberately fabricated handle is flagged [UNVERIFIED] while real…, test_audit_dossier_catches_unverified_in_client_summaries(), test_grounding_validator_fabricated_vs_verified(), test_grounding_validator_urls_and_dates(), GroundingValidator, Any (+11 more)

### Community 4 - "GroundingValidator"
Cohesion: 0.12
Nodes (14): format_markdown_report(), GroundingValidator, Any, Deterministic grounding validator for synthesis and investigation claims.…, Verify if a Twitter/X handle appears in raw evidence., Verify if a URL appears in raw evidence., Verify if a date reference is grounded in raw evidence., Perform comprehensive grounding audit on a text block (e.g. synthesis or… (+6 more)

### Community 5 - "FindingsStore"
Cohesion: 0.11
Nodes (13): FindingsStore, Any, Findings cache and state storage. Maintains findings.json to prevent re-…, Manages flat JSON storage of client investigation findings and tool evidence., Load findings from disk if file exists., Persist findings to disk., Check if client has an existing finding., Retrieve finding for a specific client. (+5 more)

### Community 6 - "SerperClient"
Cohesion: 0.19
Nodes (9): Any, Tool schemas and Serper API integration for Google Search and News. Implements…, Search Google News for press coverage., Realistic mock search results tailored for Social Capital launches., Realistic mock news results., Synchronous HTTP client for Serper.dev Google Search and News endpoints., Execute request with up to 2 retries and 1.5s * attempt backoff., Search the public web via Google. (+1 more)

### Community 7 - "SerperClient"
Cohesion: 0.17
Nodes (13): _default_news_search(), _default_web_search(), Any, Tool schemas and Serper API integration for Google Search and News. Implements…, Execute request with up to 2 retries and 1.5s * attempt backoff., Search the public web via Google., Search Google News for press coverage., Realistic mock search results tailored for Social Capital launches. (+5 more)

### Community 8 - "Investigation Summary – Airwallex Launch (AgentOS & Related Products)"
Cohesion: 0.07
Nodes (29): 1. Executive Synthesis (Cross-Launch Patterns), 1. What the data *does* show, 2. Grounding & Verification Audit Ledger, 2. What the data *does not* show, 3. Client Investigation Summaries, 3. Non-obvious pattern that emerges, 4. Run Metadata & Guardrail Statistics, Airwallex (+21 more)

### Community 9 - "app.js"
Cohesion: 0.36
Nodes (9): fallbackFindings, getStampTransform(), ledgerClaims, loadData(), parseMarkdown(), renderDossier(), renderLedger(), renderManifest() (+1 more)

### Community 10 - "PRD.md — Product Requirements Document (Hallucheck)"
Cohesion: 0.17
Nodes (11): 1. Executive Summary, 2. Problem Statement, 3. User Persona & Use Cases, 4. Scope & Dataset (The 9 Seed Clients), 5.1 ReAct Research Loop, 5.2 Cross-Launch Synthesis, 5.3 Deterministic Grounding Auditor, 5.4 Stitch UI Dashboard (+3 more)

### Community 11 - "serve.py"
Cohesion: 0.33
Nodes (3): CustomHandler, Lightweight HTTP server for the Hallucheck Stitch UI Dashboard. Run: python…, SimpleHTTPRequestHandler

### Community 12 - "agent-harness/clients.py"
Cohesion: 0.50
Nodes (3): get_clients(), Seed client data for Social Capital Inc. launches. Scraped from…, Return a copy of the 9 seed clients.

### Community 13 - "Investigation Summary – Airwallex Launch (AgentOS & Related Products)"
Cohesion: 0.07
Nodes (29): 1. Executive Synthesis (Cross-Launch Patterns), 1. What the data *does* show, 2. Grounding & Verification Audit Ledger, 2. What the data *does not* show, 3. Client Investigation Summaries, 3. Non-obvious pattern that emerges, 4. Run Metadata & Guardrail Statistics, Airwallex (+21 more)

### Community 14 - "API.md — Interface Specifications & Contracts"
Cohesion: 0.18
Nodes (10): 1. CLI Interface (`main.py`), 2.1 Route Map, 2. HTTP Server Endpoints (`serve.py`), 3.1 `web_search`, 3.2 `news_search`, 3. LLM Function Calling Schemas (`tools.py`), 4. External Services, API.md — Interface Specifications & Contracts (+2 more)

### Community 15 - "2. Core Operational Principles for AI Agents"
Cohesion: 0.20
Nodes (9): 1. Project Overview & Tech Stack, 2. Core Operational Principles for AI Agents, 3. Key Entrypoints & Commands, 4. File Ownership & Boundaries, AGENTS.md — Agent Guidelines & Repository Constraints, Rule 1: Zero Hallucination Policy (Deterministic Grounding), Rule 2: Strict Budget Management, Rule 3: Caching & Credit Conservation (+1 more)

### Community 16 - "2. Component Pipeline & Data Flow"
Cohesion: 0.22
Nodes (8): 1. High-Level System Architecture, 2. Component Pipeline & Data Flow, 3. Directory Layout & Module Responsibilities, ARCHITECTURE.md — System Architecture & Component Design, Phase 1: Investigation & Discovery (`harness.py`), Phase 2: Synthesis & Pattern Extraction (`harness.py`), Phase 3: Deterministic Grounding Audit (`validator.py`), Phase 4: Serving & Visualization (`serve.py` + `ui/`)

### Community 17 - "TASKS.md — Project Roadmap & Task Ledger"
Cohesion: 0.22
Nodes (8): 4.1 Live Streaming & Interactivity, 4.2 Expanded Investigation Scope, 4.3 Export & Sharing, 🟢 Phase 1: Core Foundation & Harness (Completed), 🟢 Phase 2: Grounding & Validation (Completed), 🟢 Phase 3: Stitch UI Dashboard (Completed), 🟡 Phase 4: Active / Upcoming Roadmap, TASKS.md — Project Roadmap & Task Ledger

### Community 18 - "2. Entity Definitions & Types"
Cohesion: 0.25
Nodes (7): 1. Persistent Storage Schema (`findings.json`), 2.1 `ClientRecord` (Seed Data), 2.2 `ToolResult`, 2.3 `ClaimAudit`, 2.4 `AuditStats`, 2. Entity Definitions & Types, SCHEMA.md — Data Models & Storage Schemas

### Community 19 - "Hallucheck — Autonomous Grounding Auditor & Investigation Package"
Cohesion: 0.11
Nodes (16): Contributing to Hallucheck, Example: Adding a `wikipedia_search` Tool, How to Add a New Tool in 3 Steps, Option A: In `tools.py`, Option B: Programmatically via `register_tool()`, Testing Your Changes, Tool Plugin Pattern, 1. Quick Start (+8 more)

### Community 20 - "deploy/app.js"
Cohesion: 0.36
Nodes (9): fallbackFindings, getStampTransform(), ledgerClaims, loadData(), parseMarkdown(), renderDossier(), renderLedger(), renderManifest() (+1 more)

### Community 21 - "test_harness.py"
Cohesion: 0.16
Nodes (16): build_investigate_prompt(), build_synthesis_prompt(), execute_tool_call(), ReAct loop, Budget management, and LLM provider abstraction. Supports Groq as…, Build the system prompt for target investigation using configurable context., Execute tool with malformed JSON / parameter validation handling. Supports…, Build the system prompt for cross-target synthesis using configurable context., Comprehensive unit and integration test suite for the Social Capital Launch-… (+8 more)

### Community 22 - "agent-harness/main.py"
Cohesion: 0.23
Nodes (9): main(), parse_args(), Main entrypoint for the Social Capital Launch-Pattern Agent Harness.…, Execute the ReAct loop for a single client up to max_turns. Tracks raw…, run_client_investigation(), Findings cache and state storage. Maintains findings.json to prevent re-…, format_markdown_report(), Deterministic grounding validator for synthesis and investigation claims.… (+1 more)

### Community 23 - "LLMClient"
Cohesion: 0.24
Nodes (8): LLMClient, Any, Call LLM with Groq as primary, falling back to OpenAI only if Groq fails., Normalize response into a clean dictionary., Realistic mock behavior for test suite and dry-runs., Run synthesis pass across all investigated clients to detect cross-launch…, Abstraction for LLM reasoning with Groq primary and OpenAI fallback., run_synthesis()

### Community 24 - "__init__.py"
Cohesion: 0.27
Nodes (9): get_clients(), load_targets(), Any, Seed client data loader. Loads targets from JSON configuration files (default:…, Load investigation configuration and target data from JSON file., Return a list of targets from the given config file., Hallucheck: Autonomous agent harness and deterministic grounding auditor.…, Verify JSON config loading and backward-compatible get_clients / CLIENTS. (+1 more)

### Community 25 - "investigate"
Cohesion: 0.29
Nodes (7): investigate(), Any, SerperClient, Run an autonomous grounded investigation over targets in a config. Args:…, LLMClient, Verify hallucheck.investigate() importable API with report object., test_investigate_library_api()

### Community 26 - "InvestigationReport"
Cohesion: 0.40
Nodes (4): InvestigationReport, Structured report produced by an investigation run., Render the complete investigation report as Markdown., Write the markdown report to a file.

### Community 28 - "main.py"
Cohesion: 0.67
Nodes (3): main(), parse_args(), Main CLI entrypoint for Hallucheck. Thin CLI wrapper delegating to the reusable…

### Community 29 - "sample_raw_tool_results"
Cohesion: 0.67
Nodes (3): fixture, Sample raw tool results representing real retrieved search/news data., sample_raw_tool_results()

## Knowledge Gaps
- **98 isolated node(s):** `fallbackFindings`, `ledgerClaims`, `fallbackFindings`, `ledgerClaims`, `1. Project Overview & Tech Stack` (+93 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 238 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `investigate()` connect `investigate` to `Budget`, `FindingsStore`, `Budget`, `GroundingValidator`, `GroundingValidator`, `FindingsStore`, `SerperClient`, `SerperClient`, `test_harness.py`, `agent-harness/main.py`, `LLMClient`, `__init__.py`, `InvestigationReport`, `main.py`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `main()` connect `agent-harness/main.py` to `Budget`, `FindingsStore`, `Budget`, `GroundingValidator`, `GroundingValidator`, `FindingsStore`, `SerperClient`, `SerperClient`, `LLMClient`, `__init__.py`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `FindingsStore` connect `FindingsStore` to `__init__.py`, `investigate`, `test_harness.py`, `agent-harness/main.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `investigate()` (e.g. with `Budget` and `LLMClient`) actually correct?**
  _`investigate()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `main()` (e.g. with `Budget` and `LLMClient`) actually correct?**
  _`main()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `fallbackFindings`, `ledgerClaims`, `fallbackFindings` to the rest of the system?**
  _98 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Budget` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._