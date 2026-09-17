# AGENTS.md — Agent Guidelines & Repository Constraints

This repository contains **Hallucheck**, an autonomous agent harness and deterministic grounding auditor designed to investigate launch patterns across stealth distribution agencies (specifically Social Capital Inc.) without hallucinated claims.

---

## 1. Project Overview & Tech Stack
- **Language**: Python 3.10+ (Standard Library + modern typing)
- **Primary Dependencies**:
  - `requests`: HTTP client for Serper.dev Google Search/News API
  - `groq`: Primary fast LLM provider for ReAct loops
  - `openai`: Fallback provider if Groq encounters rate limits or errors
  - `python-dotenv`: Environment configuration (.env)
  - `pydantic`: Schema validation
  - `pytest`: Test suite
- **Frontend / Dashboard**:
  - Vanilla HTML5, CSS3, JavaScript (ES6+), Google Fonts (Outfit & JetBrains Mono)
  - Served via native `http.server.HTTPServer` at `http://localhost:8080`

---

## 2. Core Operational Principles for AI Agents

### Rule 1: Zero Hallucination Policy (Deterministic Grounding)
All claims extracted by LLM ReAct loops (handles `@username`, dates `YYYY-MM-DD`, news URLs) **must** be cross-referenced against raw search tool results in `validator.py`.
- Never bypass the `GroundingValidator`.
- Never fabricate test findings or mock data unless explicitly running with `--mock`.

### Rule 2: Strict Budget Management
- Every tool execution (`web_search`, `news_search`) costs real API credits.
- All agent loops must respect the shared `Budget` object (default global ceiling: 60 tool calls).
- When budget is exhausted, agents must terminate search loops gracefully and proceed immediately to synthesis.

### Rule 3: Caching & Credit Conservation
- All run evidence must be committed to `findings.json` via `FindingsStore`.
- Use `--only-new` or check `store.has_client(name)` before launching investigations to avoid duplicate billable calls.

### Rule 4: Frontend UI Aesthetics
- The dashboard is located in `/ui` and served by `serve.py`.
- Maintain the Stitch aesthetic: clean dark-mode, high-contrast badges, real-time claim status filtering, and zero external JS frameworks unless requested.

---

## 3. Key Entrypoints & Commands

| Task | Command |
| :--- | :--- |
| **Run Full Investigation (Mock Mode)** | `python main.py --mock` |
| **Run Full Investigation (Live API)** | `python main.py --budget 60` |
| **Run Incremental (New Clients Only)** | `python main.py --only-new` |
| **Start Web Dashboard** | `python serve.py` (serves at http://localhost:8080) |
| **Run Automated Tests** | `pytest test_harness.py -v` |
| **Update Knowledge Graph** | `graphify update .` |

---

## 4. File Ownership & Boundaries

- `main.py`: CLI driver and pipeline orchestrator.
- `harness.py`: ReAct loop, LLM prompt engineering, budget enforcement.
- `validator.py`: Purely deterministic string & entity matching (no LLM calls allowed here).
- `store.py`: Persistence manager for `findings.json`.
- `tools.py`: Serper.dev HTTP integrations and mock payloads.
- `serve.py`: Static web server and route mapper for the UI.
- `ui/`: Client-side visualizer (HTML/CSS/JS).
