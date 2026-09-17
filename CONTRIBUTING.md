# Contributing to Hallucheck

## Tool Plugin Pattern

Hallucheck separates tool schemas from their execution logic, allowing contributors to add custom tools without modifying `harness.py` or the core agent loop.

### How to Add a New Tool in 3 Steps

To add a new tool to Hallucheck:

1. **Write the function**: Implement your tool in Python (or import it).
2. **Define the OpenAI-format schema**: Add it to `TOOL_SCHEMAS` in `tools.py`.
3. **Register the implementation**: Add it to `TOOL_IMPLEMENTATIONS` in `tools.py` (or call `register_tool`).

Nothing in `harness.py` needs to be edited. The harness automatically discovers and dispatches calls to any tool registered in `TOOL_IMPLEMENTATIONS`.

---

### Example: Adding a `wikipedia_search` Tool

#### Option A: In `tools.py`

```python
# 1. Write the function
def wikipedia_search(query: str) -> dict:
    """Look up Wikipedia summary for a topic."""
    # Example stub:
    return {
        "results": [
            {
                "title": f"Wikipedia: {query}",
                "snippet": f"Summary of Wikipedia article on {query}...",
                "link": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            }
        ]
    }

# 2. Add schema to TOOL_SCHEMAS
TOOL_SCHEMAS.append({
    "type": "function",
    "function": {
        "name": "wikipedia_search",
        "description": "Look up Wikipedia summary for a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The article search query"}
            },
            "required": ["query"]
        }
    }
})

# 3. Add to TOOL_IMPLEMENTATIONS
TOOL_IMPLEMENTATIONS["wikipedia_search"] = wikipedia_search
```

#### Option B: Programmatically via `register_tool()`

You can also register custom tools dynamically from any script or integration:

```python
from hallucheck import register_tool

wiki_schema = {
    "type": "function",
    "function": {
        "name": "wikipedia_search",
        "description": "Look up Wikipedia summary for a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The article search query"}
            },
            "required": ["query"]
        }
    }
}

def my_wiki_search(query: str):
    return {"results": [{"title": query, "snippet": "..."}]}

register_tool(wiki_schema, my_wiki_search)
```

---

## Testing Your Changes

Run the automated test suite before opening a pull request:

```bash
pytest test_harness.py -v
```
