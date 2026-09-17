# SCHEMA.md — Data Models & Storage Schemas

This document defines the schema for the persistent findings store (`findings.json`), internal data objects, and the deterministic grounding audit ledger.

---

## 1. Persistent Storage Schema (`findings.json`)

The primary data store is managed by `FindingsStore` (`store.py`). The root JSON object adheres to the following structure:

```json
{
  "metadata": {
    "version": "1.0",
    "agency": "Social Capital Inc.",
    "mode": "live",
    "provider": "groq",
    "timestamp": 1726530000,
    "budget_limit": 60,
    "budget_used": 9
  },
  "clients": {
    "PlayerZero": {
      "name": "PlayerZero",
      "launch_month": "2026-03",
      "summary": "PlayerZero launched its Series A engineering model...",
      "turns": [
        {
          "turn_index": 1,
          "role": "assistant",
          "content": "Searching for PlayerZero launch announcement...",
          "tool_calls": [
            {
              "id": "call_123",
              "name": "web_search",
              "arguments": { "query": "PlayerZero Series A launch site:x.com" }
            }
          ]
        }
      ],
      "tool_results": [
        {
          "tool": "web_search",
          "query": "PlayerZero Series A launch site:x.com",
          "result": {
            "results": [
              {
                "title": "PlayerZero Series A Announcement",
                "link": "https://x.com/playerzero/status/123",
                "snippet": "We are excited to launch our new model with @reyhanmerekar",
                "date": "2026-03-05",
                "source": "X"
              }
            ]
          }
        }
      ]
    }
  },
  "synthesis": {
    "text": "Cross-Launch Patterns across Social Capital Inc...",
    "metadata": {
      "model": "llama-3.3-70b-versatile",
      "generated_at": 1726530500
    }
  },
  "ledger": {
    "stats": {
      "total_claims": 16,
      "verified_claims": 12,
      "unverified_claims": 4,
      "grounding_score": 75.0,
      "tool_calls_used": 9,
      "budget_limit": 60
    },
    "claims": [
      {
        "context": "Synthesis",
        "type": "creator_handle",
        "claim": "@reyhanmerekar",
        "status": "verified",
        "corroboration": "Found handle @reyhanmerekar in retrieved tool results"
      },
      {
        "context": "PlayerZero",
        "type": "launch_date",
        "claim": "2026-03-12",
        "status": "unverified",
        "corroboration": "No date matching 2026-03-12 found in retrieved search results"
      }
    ]
  }
}
```

---

## 2. Entity Definitions & Types

### 2.1 `ClientRecord` (Seed Data)
| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | `string` | Official brand or product name (e.g. `"Wispr Flow"`). |
| `launch_month` | `string` | Target launch period in format `YYYY-MM`. |

### 2.2 `ToolResult`
| Field | Type | Description |
| :--- | :--- | :--- |
| `tool` | `string` | Tool name (`"web_search"` or `"news_search"`). |
| `query` | `string` | Executed query string including site filters. |
| `result` | `object` | Raw Serper JSON payload containing search result list. |

### 2.3 `ClaimAudit`
| Field | Type | Values / Description |
| :--- | :--- | :--- |
| `context` | `string` | Source section: `"Synthesis"` or Client Name. |
| `type` | `string` | `"creator_handle"`, `"launch_date"`, or `"url"`. |
| `claim` | `string` | The extracted entity text (e.g. `"@Rahul_J_Mathur"`). |
| `status` | `string` | `"verified"` (green) or `"unverified"` (amber flagged). |
| `corroboration` | `string` | Detailed explanation of snippet match or failure to locate. |

### 2.4 `AuditStats`
| Metric | Type | Description |
| :--- | :--- | :--- |
| `grounding_score` | `float` | Percentage of verified claims over total extracted claims. |
| `verified_claims` | `int` | Count of claims matched against raw evidence. |
| `unverified_claims`| `int` | Count of claims flagged as uncorroborated. |
| `tool_calls_used` | `int` | Count of actual API calls consumed. |
