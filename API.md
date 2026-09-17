# API.md — Interface Specifications & Contracts

This document outlines the command-line interfaces, internal HTTP endpoints, and tool function schemas for **Hallucheck**.

---

## 1. CLI Interface (`main.py`)

The pipeline is invoked through `python main.py` with the following flags:

```bash
python main.py [OPTIONS]
```

### Options & Arguments
| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--mock` | `boolean` | `false` | Run in offline simulation mode without consuming live API credits. |
| `--only-new` | `boolean` | `false` | Skip clients already present with completed summaries in `findings.json`. |
| `--budget` | `integer` | `60` | Global maximum tool executions across all clients and synthesis. |
| `--limit` | `integer` | `None` | Restrict number of seed clients to investigate (e.g. `--limit 3`). |
| `--store` | `string` | `"findings.json"` | Path to JSON cache file. |
| `--output` | `string` | `"report.md"` | Destination file path for generated Markdown audit report. |

---

## 2. HTTP Server Endpoints (`serve.py`)

The local server runs via `python serve.py` on `http://localhost:8080`.

### 2.1 Route Map
| Route | Method | MIME Type | Description |
| :--- | :--- | :--- | :--- |
| `/` or `/index.html` | `GET` | `text/html` | Serves `ui/index.html` (Stitch UI dashboard). |
| `/ui/*` | `GET` | Static assets | Serves CSS, JS, and UI static assets. |
| `/style.css` | `GET` | `text/css` | Main dashboard stylesheet. |
| `/app.js` | `GET` | `application/javascript` | Client-side dashboard logic and state management. |
| `/findings.json` | `GET` | `application/json` | Serves current raw findings, client turns, and audit ledger. |
| `/report.md` | `GET` | `text/markdown` | Serves compiled markdown report for viewing or downloading. |

---

## 3. LLM Function Calling Schemas (`tools.py`)

The ReAct harness provides the following function definitions to Groq / OpenAI:

### 3.1 `web_search`
Searches the public web via Google through Serper.dev.
```json
{
  "name": "web_search",
  "description": "Search the public web via Google. Use site: filters (e.g. 'site:x.com' or 'site:linkedin.com/posts') to narrow results to a specific platform. Returns organic results with title, link, and snippet.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query, including any site: filters."
      },
      "num_results": {
        "type": "integer",
        "description": "How many results to return (default 10, max 20)."
      }
    },
    "required": ["query"]
  }
}
```

### 3.2 `news_search`
Queries Google News for press coverage and media announcements.
```json
{
  "name": "news_search",
  "description": "Search Google News for press coverage of a topic, e.g. a product launch. Useful for pinning down exact launch dates and finding named creators/journalists who covered it.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The news search query."
      }
    },
    "required": ["query"]
  }
}
```

---

## 4. External Services

### Serper.dev HTTP API
- **Endpoint**: `POST https://google.serper.dev/search` or `POST https://google.serper.dev/news`
- **Headers**:
  - `X-API-KEY`: Serper API Key
  - `Content-Type`: `application/json`
- **Retry Policy**: 2 retries with exponential backoff ($1.5 \times \text{attempt}$ seconds).
