# PRD.md — Product Requirements Document (Hallucheck)

## 1. Executive Summary
**Hallucheck** is an automated research and grounding audit platform. It autonomously investigates how stealth marketing and distribution agencies (specifically Social Capital Inc.) launch software products across social platforms (LinkedIn and X), synthesizes cross-launch patterns, and deterministically audits every asserted claim against raw search evidence to prevent AI hallucinations.

---

## 2. Problem Statement
Large Language Models (LLMs) used in automated market intelligence frequently hallucinate:
1. **Fabricated Handles**: Inventing creator or influencer handles (e.g. `@tech_guru`) to support a narrative.
2. **False Launch Dates**: Hallucinating calendar days without corroborated timestamps.
3. **Phantom Links**: Citing non-existent press releases or blogs.
4. **Premature Generalization**: Over-interpreting sparse data to claim a "universal playbook" exists when evidence is thin.

Hallucheck solves this by separating **Autonomous Discovery (ReAct)** from **Deterministic Grounding Verification (Zero-LLM regex/entity indexing)**.

---

## 3. User Persona & Use Cases
- **Growth Investors & Founders**: Analyzing whether viral launch spikes are organic or driven by coordinated agency amplification.
- **Product Marketers**: Reverse-engineering the exact timing, distribution channels, and creator rosters used across top-tier B2B launches.
- **Fact-Checking & Compliance Analysts**: Requiring deterministic audit trails showing which claims have raw API citations and which are unverified assertions.

---

## 4. Scope & Dataset (The 9 Seed Clients)
Hallucheck seeds investigations from 9 verified product launches executed by Social Capital Inc.:
1. **PlayerZero** (2026-03)
2. **Wispr Flow** (2026-02)
3. **Poly AI** (2026-02)
4. **Airwallex** (2025-12)
5. **Gamma** (2025-11)
6. **Cartesia** (2025-10)
7. **Deel** (2025-10)
8. **Superblocks** (2025-05)
9. **Icon** (2025-02)

---

## 5. Functional Requirements

### 5.1 ReAct Research Loop
- Autonomous iterative query formulation (Google Web Search, Google News Search via Serper API).
- Platform-specific filtering (`site:x.com`, `site:linkedin.com/posts`).
- Maximum turns per client investigation (typically 3 to 6 turns).
- Global Budget counter enforcing credit limits.

### 5.2 Cross-Launch Synthesis
- Aggregates findings across all analyzed clients.
- Identifies cross-cutting non-obvious patterns:
  - Launch-day burst windows (24–48 hours).
  - Platform reliance (LinkedIn vs X).
  - Creator roster overlap.
  - Media coverage vs grassroots amplification.
- Explicitly reports **what the data does NOT show** to avoid over-claiming.

### 5.3 Deterministic Grounding Auditor
- Extracts all specific entities from the generated synthesis and client summaries:
  - Creator handles (`@handle` or URL paths)
  - Specific calendar dates (`YYYY-MM-DD` or formal date strings)
  - Press and article URLs
- Tests each entity against the raw corpus of search tool snippets.
- Produces a **Grounding Score**:
  $$\text{Grounding Score} = \frac{\text{Verified Claims}}{\text{Verified Claims} + \text{Unverified Claims}} \times 100\%$$
- Emits warnings for any claim that cannot be corroborated.

### 5.4 Stitch UI Dashboard
- Responsive local dashboard served at `http://localhost:8080`.
- Visual KPI cards (Grounding Score, Verified Claims, Tool Calls Used).
- Interactive Ledger with real-time filtering (All, Verified Only, Flagged Only).
- Direct side-by-side view of Synthesis vs. Grounded Evidence.

---

## 6. Non-Goals (Out of Scope)
- **Direct Social Platform Scraping**: We do not scrape behind authenticated paywalls/login walls of X or LinkedIn directly; we rely on Google-indexed public snippets via Serper.
- **Automated Social Posting**: Hallucheck only investigates and audits; it does not draft or publish social media posts.
- **Non-Deterministic Fuzzy Fact-Checking**: The validator strictly does not use LLM prompts for judging truth; verification is 100% deterministic against raw HTTP response bodies.
