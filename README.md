# Hallucheck — Autonomous Grounding Auditor & Investigation Package

Hallucheck is an autonomous agent harness and deterministic grounding auditor designed to run cross-target investigations without hallucinated claims. Every handle, date, and URL asserted by the LLM reasoning loop is cross-referenced against raw search tool traces.

---

## 1. Quick Start

### Installation & Configuration

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API keys in `.env`**:
   ```ini
   GROQ_API_KEY=your_groq_key_here
   SERPER_API_KEY=your_serper_key_here
   # Optional fallback:
   OPENAI_API_KEY=your_openai_key_here
   ```

3. **Run investigation via CLI**:
   ```bash
   # Default investigation (Social Capital Inc. launch forensics)
   python main.py --config configs/social_capital.json

   # Skip already-cached targets (conserves API credits)
   python main.py --only-new

   # Offline mock simulation (zero billable API credits)
   python main.py --mock
   ```

---

## 2. Use as a Library

Hallucheck can be imported and invoked programmatically from any Python application without going through the CLI:

### Function Signature
```python
def investigate(
    config_path: str = "configs/social_capital.json",
    provider: str = "groq",
    budget_max_calls: int = 60,
    mock: bool = False,
    only_new: bool = False,
    limit: Optional[int] = None,
    store_path: Optional[str] = "findings.json",
    output_report_path: Optional[str] = "report.md",
    custom_tools: Optional[List[Dict[str, Any]]] = None,
    custom_implementations: Optional[Dict[str, Callable]] = None,
) -> InvestigationReport
```

### 5-Line Usage Example
```python
from hallucheck import investigate

# Run an investigation programmatically
report = investigate("configs/example_competitor_research.json", mock=True)

# Access findings, synthesis, and grounding audit
print(f"Grounding Score: {report.stats['grounding_score_percent']}%")
print(f"Verified Claims: {report.stats['verified_count']} / {report.stats['total_claims']}")
print(report.to_markdown()[:300])
```

The returned `InvestigationReport` dataclass provides:
- `report.findings`: Per-target structured findings dictionary.
- `report.synthesis`: Cross-target synthesis text.
- `report.ledger`: List of audited claims with verification status and raw source snippets.
- `report.stats`: Dict containing `grounding_score_percent`, `verified_count`, `unverified_count`, `total_claims`.
- `report.budget`: Usage tracking dict (`used`, `max`, `remaining`).
- `report.to_markdown()`: Generates the full formatted markdown audit report.
- `report.to_json()`: Serializes all evidence and audit logs to JSON.

---

## 3. Add Your Own Investigation

Hallucheck generalizes to any multi-target research domain. To run a new investigation, create a JSON config in `configs/`:

```json
{
  "investigation_name": "AI Code Assistant Competitor Pricing & Packaging",
  "context": "pricing tiers, enterprise packaging, and free tier limits of AI developer tools",
  "synthesis_context": "competitor pricing models across the code assistant market",
  "targets": [
    {"name": "Cursor", "domain": "cursor.com"},
    {"name": "GitHub Copilot", "domain": "github.com"},
    {"name": "Codeium", "domain": "codeium.com"},
    {"name": "Tabnine", "domain": "tabnine.com"}
  ]
}
```

Run it via the CLI:
```bash
python main.py --config configs/my_investigation.json --budget 40
```

---

## 4. Tool Plugin Pattern

Hallucheck allows developers to introduce new tools in 3 steps without modifying `harness.py`:

1. Write the Python function.
2. Add its OpenAI schema to `TOOL_SCHEMAS` in `tools.py`.
3. Add the callable to `TOOL_IMPLEMENTATIONS` in `tools.py` (or call `register_tool(schema, func)`).

See [CONTRIBUTING.md](CONTRIBUTING.md) for full documentation and a `wikipedia_search` code example.

---

## 5. Web Dashboard & Testing

- **Launch Paper-Audit Dossier UI**:
  ```bash
  python serve.py
  # Serves at http://localhost:8080/ui/index.html
  ```

- **Run Automated Test Suite**:
  ```bash
  pytest test_harness.py -v
  ```
