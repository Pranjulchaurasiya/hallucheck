# TASKS.md — Project Roadmap & Task Ledger

This document tracks completed milestones, active capabilities, and upcoming engineering tasks for **Hallucheck**.

---

## 🟢 Phase 1: Core Foundation & Harness (Completed)
- [x] **Seed Data Ingestion**: Scraped 9 confirmed portfolio clients from `sociallcapital.com/work` ([clients.py](file:///c:/Users/pranj/Documents/Hallucheck/clients.py)).
- [x] **Serper Client & Tools**: Implemented `web_search` and `news_search` tools with retry backoff and mock capabilities ([tools.py](file:///c:/Users/pranj/Documents/Hallucheck/tools.py)).
- [x] **Budget Enforcement**: Global budget counter preventing API credit overruns across client loops ([harness.py](file:///c:/Users/pranj/Documents/Hallucheck/harness.py)).
- [x] **Multi-LLM Provider Support**: Fast Groq execution with automatic fallback to OpenAI ([harness.py](file:///c:/Users/pranj/Documents/Hallucheck/harness.py)).
- [x] **ReAct Loop**: Autonomous search, reasoning, and summarization per client ([harness.py](file:///c:/Users/pranj/Documents/Hallucheck/harness.py)).

---

## 🟢 Phase 2: Grounding & Validation (Completed)
- [x] **Deterministic Corpus Construction**: Flatten and index URLs, domains, and `@handles` from raw Serper JSON results ([validator.py](file:///c:/Users/pranj/Documents/Hallucheck/validator.py)).
- [x] **Entity & Claim Extraction**: Regex parsers for handles, dates, and citations without LLM hallucination risk.
- [x] **Grounding Score Metric**: Compute deterministic grounding percentages ($100 \times \frac{\text{Verified}}{\text{Total}}$).
- [x] **Markdown Report Generator**: Export structured reports with executive synthesis and verified/unverified claim audit tables ([report.md](file:///c:/Users/pranj/Documents/Hallucheck/report.md)).
- [x] **Persistent Caching**: Store completed investigations in `findings.json` to prevent duplicate API expenses ([store.py](file:///c:/Users/pranj/Documents/Hallucheck/store.py)).

---

## 🟢 Phase 3: Stitch UI Dashboard (Completed)
- [x] **Local HTTP Server**: Python `http.server` running on port 8080 with clean route translation ([serve.py](file:///c:/Users/pranj/Documents/Hallucheck/serve.py)).
- [x] **Single-Page Dashboard**: Stitch aesthetic with dark mode, KPI summary cards, and tabs ([ui/index.html](file:///c:/Users/pranj/Documents/Hallucheck/ui/index.html)).
- [x] **Interactive Audit Ledger**: Filter claims by All, Verified, and Flagged status ([ui/app.js](file:///c:/Users/pranj/Documents/Hallucheck/ui/app.js)).
- [x] **Automated Test Suite**: Unit and integration tests covering budget, mock tools, store, and validator ([test_harness.py](file:///c:/Users/pranj/Documents/Hallucheck/test_harness.py)).

---

## 🟡 Phase 4: Active / Upcoming Roadmap

### 4.1 Live Streaming & Interactivity
- [ ] **Server-Sent Events (SSE)**: Add SSE endpoint in `serve.py` so running `main.py` broadcasts live tool calls and thoughts directly to the UI dashboard in real time.
- [ ] **Dashboard Run Trigger**: Add a "Start Investigation" button in the Stitch UI to trigger runs directly from the browser without opening a terminal.

### 4.2 Expanded Investigation Scope
- [ ] **Full 9-Client Live Run**: Execute live investigation across the remaining 6 clients (Airwallex, Gamma, Cartesia, Deel, Superblocks, Icon) while respecting the 60-call budget.
- [ ] **Cross-Platform Scheduling Parser**: Extract posting timestamps from snippets to construct an hour-by-hour launch day timeline.

### 4.3 Export & Sharing
- [ ] **PDF Export**: Generate downloadable, publication-grade PDF dossiers from `report.md`.
- [ ] **SQLite Backend**: Optional migration of `findings.json` to a local SQLite database for SQL-based analytical queries.
