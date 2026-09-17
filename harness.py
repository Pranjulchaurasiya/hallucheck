"""ReAct loop, Budget management, and LLM provider abstraction.

Supports Groq as primary LLM provider with fallback to OpenAI if Groq retries fail.
Includes Budget tracking, tool execution with error recovery, and mock simulation mode.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from tools import TOOL_SCHEMAS, TOOL_IMPLEMENTATIONS, SerperClient, bind_serper_client

logger = logging.getLogger(__name__)

DEFAULT_INVESTIGATE_CONTEXT = (
    "how a stealth marketing/distribution\nagency executes product launches on X and LinkedIn"
)
DEFAULT_SYNTHESIS_CONTEXT = (
    "product launches run\nby the same distribution agency"
)


def build_investigate_prompt(context: Optional[str] = None) -> str:
    """Build the system prompt for target investigation using configurable context."""
    ctx = context or DEFAULT_INVESTIGATE_CONTEXT
    return f"""You are a research analyst investigating {ctx}. You have web_search and
news_search tools backed by Google's index (use site:x.com or
site:linkedin.com/posts filters to narrow platform).

For the given client, find:
1. Roughly when their launch happened and what press/posts covered it.
2. Any recurring named creators/accounts that posted about it (list handles
if you find them).
3. Anything notable about post structure/timing (e.g. multiple accounts
posting within a short window, a consistent narrative arc).

Be honest about what you could NOT find — don't invent handles or dates. End
with a short structured summary."""


def build_synthesis_prompt(context: Optional[str] = None) -> str:
    """Build the system prompt for cross-target synthesis using configurable context."""
    ctx = context or DEFAULT_SYNTHESIS_CONTEXT
    return f"""You are synthesizing research findings across multiple {ctx}. You will be given per-client findings. Your
job is to find the NON-OBVIOUS pattern: what's repeated across launches that
wouldn't be obvious from looking at any single one. E.g. recurring creator
handles, consistent timing/structure, a repeatable playbook.

If the underlying data is too thin to support a real conclusion, say so
plainly rather than overreaching. A honest "here's what the data does and
doesn't support" beats a confident guess."""


INVESTIGATE_SYSTEM_PROMPT = build_investigate_prompt()
SYNTHESIS_SYSTEM_PROMPT = build_synthesis_prompt()


class Budget:
    """A single shared counter across the whole run (all clients + synthesis)."""

    def __init__(self, max_tool_calls: int = 60):
        self.max_tool_calls = max_tool_calls
        self.tool_calls_used = 0

    def can_consume(self) -> bool:
        """Check if any tool budget remains."""
        return self.tool_calls_used < self.max_tool_calls

    def consume(self) -> bool:
        """Consume 1 unit of budget if available. Returns True if granted, False if exhausted."""
        if self.tool_calls_used < self.max_tool_calls:
            self.tool_calls_used += 1
            return True
        return False

    def is_exhausted(self) -> bool:
        """Return whether the budget is fully spent."""
        return self.tool_calls_used >= self.max_tool_calls

    @property
    def remaining(self) -> int:
        """Remaining allowed tool calls."""
        return max(0, self.max_tool_calls - self.tool_calls_used)


class LLMClient:
    """Abstraction for LLM reasoning with Groq primary and OpenAI fallback."""

    def __init__(self, mock: bool = False):
        self.mock = mock
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        self.groq_client = None
        self.openai_client = None

        if not self.mock:
            if self.groq_api_key:
                try:
                    from groq import Groq
                    self.groq_client = Groq(api_key=self.groq_api_key)
                except Exception as e:
                    logger.warning(f"Could not initialize Groq client: {e}")
            if self.openai_api_key:
                try:
                    from openai import OpenAI
                    self.openai_client = OpenAI(api_key=self.openai_api_key)
                except Exception as e:
                    logger.warning(f"Could not initialize OpenAI client: {e}")

    def call(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Call LLM with Groq as primary, falling back to OpenAI only if Groq fails."""
        if self.mock:
            return self._mock_llm_response(messages, tools)

        # Primary: Groq
        groq_err = None
        if self.groq_client:
            models_to_try = [
                getattr(self, "_working_groq_model", None) or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                "openai/gpt-oss-120b",
                "llama-3.3-70b-versatile"
            ]
            # De-duplicate while preserving order
            seen_models = set()
            models_to_try = [m for m in models_to_try if m and not (m in seen_models or seen_models.add(m))]

            for model_name in models_to_try:
                for attempt in range(1, 3):
                    try:
                        kwargs: Dict[str, Any] = {
                            "model": model_name,
                            "messages": messages,
                            "temperature": temperature
                        }
                        if tools:
                            kwargs["tools"] = tools
                            if tool_choice and tool_choice != "none":
                                kwargs["tool_choice"] = tool_choice
                        resp = self.groq_client.chat.completions.create(**kwargs)
                        self._working_groq_model = model_name
                        return self._normalize_response(resp)
                    except Exception as e:
                        groq_err = e
                        err_str = str(e).lower()
                        if "does not exist" in err_str or "not_found" in err_str or "404" in err_str:
                            logger.info(f"Groq model '{model_name}' not available on account. Trying next candidate...")
                            break
                        logger.warning(f"Groq API call ({model_name}) attempt {attempt} failed: {e}")
                        time.sleep(1.0 * attempt)

        # Fallback to OpenAI only if Groq failed or wasn't configured
        if self.openai_client:
            logger.info("Falling back to OpenAI after Groq exhaustion...")
            try:
                kwargs = {
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": temperature
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice
                resp = self.openai_client.chat.completions.create(**kwargs)
                return self._normalize_response(resp)
            except Exception as e:
                logger.error(f"OpenAI fallback call also failed: {e}")
                raise RuntimeError(f"Both Groq and OpenAI failed. Groq error: {groq_err}; OpenAI error: {e}") from e

        # If we reach here and have no working provider
        if groq_err:
            raise RuntimeError(f"Groq failed after retries and no OpenAI fallback available: {groq_err}") from groq_err
        raise ValueError("Neither GROQ_API_KEY nor OPENAI_API_KEY is configured, and mock mode is False.")

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        """Normalize response into a clean dictionary."""
        choice = response.choices[0]
        message = choice.message
        tool_calls = []
        if getattr(message, "tool_calls", None):
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        return {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": tool_calls
        }

    def _mock_llm_response(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Realistic mock behavior for test suite and dry-runs."""
        user_msgs = [m for m in messages if m.get("role") == "user"]
        assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
        tool_msgs = [m for m in messages if m.get("role") == "tool"]

        # Check if this is a synthesis call
        if any("synthesizing research findings" in str(m.get("content", "")).lower() for m in messages if m.get("role") == "system"):
            synthesis_text = (
                "### Executive Synthesis: Cross-Launch Distribution Patterns\n\n"
                "After analyzing all 9 client launches orchestrated by Social Capital Inc. across X and LinkedIn, "
                "the following non-obvious patterns emerge:\n\n"
                "1. **Core Influencer Amplification Ring**:\n"
                "   Across AI and developer tooling clients (PlayerZero, Wispr Flow, Poly AI, Cartesia), "
                "   the agency consistently engaged a tight creator cohort including @swyx, @packyM, and @gregisenberg. "
                "   These creators did not simply retweet corporate announcements; they published personal teardowns, "
                "   live audio/video trials, and interactive demos.\n\n"
                "2. **48-Hour Multi-Platform Blitz Architecture**:\n"
                "   Rather than a rolling awareness campaign, launches exhibit extreme temporal clustering: "
                "   a coordinated primary video/thread on X, synchronized with LinkedIn executive commentary "
                "   within a 4 to 12 hour window (e.g. Gamma in November 2025, Wispr Flow on February 12, 2026).\n\n"
                "3. **What the Data Does NOT Support**:\n"
                "   The data does NOT support a single unified agency watermark or explicit agency tag. "
                "   Furthermore, non-AI clients (such as Deel and Icon) utilized distinct creator networks tailored "
                "   specifically to HR compliance and industrial hardware rather than developer tech.\n\n"
                "4. **Verified Launch Timeline References**:\n"
                "   - PlayerZero: Launched in March 2026 (coverage: https://techcrunch.com/2026/03/05/playerzero-launch)\n"
                "   - Wispr Flow: Launched on February 12, 2026 (announced with @swyx and @gregisenberg)\n"
                "   - Cartesia: Flagship Sonic model launched in October 2025\n"
                "   - Gamma: 2.0 release in November 2025 with interactive decks\n"
            )
            return {"role": "assistant", "content": synthesis_text, "tool_calls": []}

        # Client investigation loop
        client_name = ""
        for m in user_msgs:
            c = m.get("content", "")
            if "Client:" in c:
                client_name = c.split("Client:")[1].split("\n")[0].strip()
                break

        # If tools are disabled (budget exhausted) or we already made 2 tool queries, return final structured answer
        if not tools or len(tool_msgs) >= 2:
            content = (
                f"### Research Findings for {client_name}\n"
                f"- **Launch Timing**: Documented launch occurred around client target timeline with multi-channel coverage.\n"
                f"- **Named Creators & Handles**: Significant engagement observed from key accounts including @swyx, @packyM, @sama, and @gregisenberg.\n"
                f"- **Post Structure & Timing**: Coordinated multi-creator announcements within a tight 48-hour window on X, followed by LinkedIn case studies.\n"
                f"- **Limitations / Gaps**: No explicit public mention of Social Capital contract terms directly on-post; attribution inferred from timing & network cluster."
            )
            return {"role": "assistant", "content": content, "tool_calls": []}

        # First turn: trigger web_search
        if len(tool_msgs) == 0:
            return {
                "role": "assistant",
                "content": f"I will search for {client_name}'s product launch on X and LinkedIn.",
                "tool_calls": [
                    {
                        "id": f"call_{int(time.time()*1000)}_1",
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "arguments": json.dumps({"query": f"{client_name} launch site:x.com OR site:linkedin.com/posts", "num_results": 5})
                        }
                    }
                ]
            }
        
        # Second turn: trigger news_search
        return {
            "role": "assistant",
            "content": f"I will check Google News coverage for {client_name} launch dates and press releases.",
            "tool_calls": [
                {
                    "id": f"call_{int(time.time()*1000)}_2",
                    "type": "function",
                    "function": {
                        "name": "news_search",
                        "arguments": json.dumps({"query": f"{client_name} launch date product announcement"})
                    }
                }
            ]
        }


def execute_tool_call(
    tool_name: str,
    raw_args: str,
    serper_client: Optional[SerperClient] = None,
    tool_implementations: Optional[Dict[str, Callable]] = None
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Execute tool with malformed JSON / parameter validation handling.

    Supports dynamic tool dispatch via tool_implementations (or TOOL_IMPLEMENTATIONS).
    Returns:
        (result_data, error_string_for_llm_if_any)
    """
    logger.info(f"Executing tool '{tool_name}' with args: {raw_args}")
    try:
        parsed_args = json.loads(raw_args)
    except json.JSONDecodeError as e:
        err_msg = f"Tool call error: Malformed JSON arguments. {str(e)}. Please format arguments as valid JSON."
        return {"error": err_msg}, err_msg

    if not isinstance(parsed_args, dict):
        err_msg = "Tool call error: Arguments must be a JSON dictionary."
        return {"error": err_msg}, err_msg

    if "query" not in parsed_args or not parsed_args["query"]:
        err_msg = "Tool call error: Missing required parameter 'query'."
        return {"error": err_msg}, err_msg

    if serper_client is not None:
        bind_serper_client(serper_client)

    impls = tool_implementations or TOOL_IMPLEMENTATIONS
    if tool_name not in impls:
        available = ", ".join(impls.keys())
        err_msg = f"Tool call error: Unknown tool '{tool_name}'. Available tools: {available}."
        return {"error": err_msg}, err_msg

    try:
        fn = impls[tool_name]
        res = fn(**parsed_args)
        return res, None
    except TypeError as te:
        err_msg = f"Tool call error: Invalid parameters for tool '{tool_name}': {te}"
        return {"error": err_msg}, err_msg
    except Exception as e:
        err_msg = f"Tool call execution failed: {str(e)}"
        return {"error": err_msg}, err_msg


def run_client_investigation(
    client: Dict[str, str],
    budget: Budget,
    serper_client: SerperClient,
    llm_client: LLMClient,
    max_turns: int = 12,
    investigate_prompt: Optional[str] = None,
    tool_schemas: Optional[List[Dict[str, Any]]] = None,
    tool_implementations: Optional[Dict[str, Callable]] = None
) -> Dict[str, Any]:
    """Execute the ReAct loop for a single client up to max_turns.

    Tracks raw tool_results separately for grounding validation.
    Enforces shared budget guardrail across all tool calls.
    """
    client_name = client["name"]
    launch_month = client.get("launch_month", "Unknown")
    logger.info(f"Starting investigation for {client_name} (Launch: {launch_month})")

    prompt = investigate_prompt or INVESTIGATE_SYSTEM_PROMPT
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                f"Client: {client_name}\n"
                f"Target Launch Month: {launch_month}\n\n"
                f"Investigate this product launch on X and LinkedIn following the instructions. "
                f"Find when the launch happened, creator handles, and post timing/structure."
            )
        }
    ]

    tool_results: List[Dict[str, Any]] = []
    turns_taken = 0
    status = "completed"
    final_summary = ""

    for turn in range(1, max_turns + 1):
        turns_taken = turn

        # Determine if tool calling is allowed by budget and turn count
        tools_available = tool_schemas if tool_schemas is not None else TOOL_SCHEMAS

        # If budget exhausted or final turn reached, force LLM to formulate final summary
        if (turn == max_turns or budget.is_exhausted()) and not any("final structured summary" in str(m.get("content", "")).lower() for m in messages):
            messages.append({
                "role": "system",
                "content": "You have reached your search limit for this client. Please provide your final structured summary now based solely on the data gathered so far."
            })

        try:
            response = llm_client.call(
                messages=messages,
                tools=tools_available,
                tool_choice="auto"
            )
        except Exception as e:
            logger.error(f"Error calling LLM for {client_name} on turn {turn}: {e}")
            final_summary = f"Investigation halted due to LLM error: {e}"
            status = "incomplete"
            break

        assistant_msg = {
            "role": "assistant",
            "content": response.get("content") or "",
        }
        if response.get("tool_calls"):
            assistant_msg["tool_calls"] = response["tool_calls"]
        messages.append(assistant_msg)

        # Check if the LLM provided tool calls
        tool_calls = response.get("tool_calls", [])
        if not tool_calls or turn >= max_turns:
            if not tool_calls:
                final_summary = response.get("content", "").strip()
                status = "completed"
                break
            else:
                # Model called a tool on the final turn: satisfy tool calls and get final text summary
                for tc in tool_calls:
                    call_id = tc.get("id", "call_unknown")
                    func_obj = tc.get("function", {})
                    func_name = func_obj.get("name", "tool")
                    messages.append({
                        "tool_call_id": call_id,
                        "role": "tool",
                        "name": func_name,
                        "content": json.dumps({"notice": "Turn limit reached. Please output your final structured markdown summary now."})
                    })
                try:
                    summary_resp = llm_client.call(messages=messages, tools=tools_available)
                    final_summary = summary_resp.get("content", "").strip()
                    status = "completed"
                except Exception as e:
                    logger.warning(f"Failed to fetch final summary on turn {turn}: {e}")
                    final_summary = response.get("content", "").strip() or "Summary generated from tool observations."
                    status = "completed"
                break

        # Execute each requested tool call
        for tc in tool_calls:
            call_id = tc.get("id", "call_unknown")
            func_obj = tc.get("function", {})
            func_name = func_obj.get("name", "")
            raw_args = func_obj.get("arguments", "{}")

            # Check budget before executing
            if not budget.consume():
                # Budget exhausted
                tool_output_str = json.dumps({
                    "error": "Global tool call budget exhausted. Further tool calls are blocked. Conclude your answer now."
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": tool_output_str
                })
                continue

            # Execute tool safely via dynamic tool implementations
            raw_result, error_str = execute_tool_call(
                func_name,
                raw_args,
                serper_client=serper_client,
                tool_implementations=tool_implementations
            )

            # Store raw result for deterministic grounding validator
            tool_entry = {
                "client": client_name,
                "tool": func_name,
                "arguments": raw_args,
                "result": raw_result,
                "error": error_str,
                "turn": turn
            }
            tool_results.append(tool_entry)

            # Format tool response for message history
            if error_str:
                tool_content = json.dumps({"error": error_str})
            else:
                compact_results = []
                for item in raw_result.get("results", [])[:5]:
                    compact_results.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "")[:300],
                        "date": item.get("date", "")
                    })
                tool_content = json.dumps({"results": compact_results}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": tool_content
            })

    else:
        # Loop reached max_turns without final answer
        status = "incomplete"
        logger.warning(f"Client {client_name} reached MAX_TURNS ({max_turns}). Marking as incomplete.")
        if not final_summary:
            # Extract last assistant content if available
            last_content = [m.get("content") for m in messages if m.get("role") == "assistant" and m.get("content")]
            final_summary = last_content[-1] if last_content else "Investigation timed out after 12 turns."

    return {
        "client": client_name,
        "launch_month": launch_month,
        "status": status,
        "turns_taken": turns_taken,
        "summary": final_summary,
        "tool_results": tool_results,
        "message_count": len(messages)
    }


def run_synthesis(
    all_findings: Dict[str, Any],
    llm_client: LLMClient,
    synthesis_prompt: Optional[str] = None
) -> str:
    """Run synthesis pass across all investigated clients to detect cross-launch patterns."""
    logger.info("Executing cross-client pattern synthesis pass...")

    findings_summary_blocks = []
    for client_name, data in all_findings.items():
        summary = data.get("summary") or data.get("annotated_summary") or "No summary recorded"
        if len(summary) > 750:
            summary = summary[:750] + "..."
        status = data.get("status", "unknown")
        launch = data.get("launch_month", "unknown")
        findings_summary_blocks.append(
            f"### Client: {client_name} (Launch: {launch}, Status: {status})\n{summary}\n"
        )

    all_data_str = "\n".join(findings_summary_blocks)

    prompt = synthesis_prompt or SYNTHESIS_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                "Here are the research findings for all clients investigated:\n\n"
                f"{all_data_str}\n\n"
                "Synthesize these findings according to instructions. Look for non-obvious patterns, "
                "recurring creators/handles, timing clustering, and specify what the data does and does NOT support."
            )
        }
    ]

    resp = llm_client.call(messages=messages, tools=None)
    return resp.get("content", "").strip()
