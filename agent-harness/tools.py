"""Tool schemas and Serper API integration for Google Search and News.

Implements web_search and news_search endpoints with backoff retries and mock capabilities.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the public web via Google. Use site: filters (e.g. 'site:x.com' or 'site:linkedin.com/posts') to narrow results to a specific platform. Returns organic results with title, link, and snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query, including any site: filters."},
                    "num_results": {"type": "integer", "description": "How many results to return (default 10, max 20)."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "news_search",
            "description": "Search Google News for press coverage of a topic, e.g. a product launch. Useful for pinning down exact launch dates and finding named creators/journalists who covered it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The news search query."}
                },
                "required": ["query"]
            }
        }
    }
]


class SerperClient:
    """Synchronous HTTP client for Serper.dev Google Search and News endpoints."""

    BASE_URL = "https://google.serper.dev"

    def __init__(self, api_key: Optional[str] = None, mock: bool = False):
        self.api_key = api_key or os.getenv("SERPER_API_KEY", "")
        self.mock = mock
        if not self.mock and not self.api_key:
            logger.warning("SERPER_API_KEY is not set. Tools will fail unless in mock mode.")

    def _execute_with_retry(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute request with up to 2 retries and 1.5s * attempt backoff."""
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        max_attempts = 3
        last_err = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_err = e
                if attempt < max_attempts:
                    sleep_time = 1.5 * attempt
                    logger.warning(
                        f"Serper request failed on attempt {attempt}/{max_attempts}: {e}. "
                        f"Retrying in {sleep_time:.1f}s..."
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Serper request exhausted all {max_attempts} attempts: {e}")
                    raise RuntimeError(f"Serper API error after retries: {last_err}") from last_err

        return {}

    def web_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """Search the public web via Google."""
        num_results = min(max(int(num_results), 1), 20)
        if self.mock:
            return self._mock_web_search(query, num_results)

        payload = {"q": query, "num": num_results}
        data = self._execute_with_retry("search", payload)
        
        # Normalize response
        organic = data.get("organic", [])
        return {
            "query": query,
            "results": [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "position": item.get("position", idx + 1)
                }
                for idx, item in enumerate(organic[:num_results])
            ]
        }

    def news_search(self, query: str) -> Dict[str, Any]:
        """Search Google News for press coverage."""
        if self.mock:
            return self._mock_news_search(query)

        payload = {"q": query}
        data = self._execute_with_retry("news", payload)
        
        news = data.get("news", [])
        return {
            "query": query,
            "results": [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "date": item.get("date", ""),
                    "source": item.get("source", "")
                }
                for item in news[:10]
            ]
        }

    def _mock_web_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Realistic mock search results tailored for Social Capital launches."""
        q_lower = query.lower()
        results: List[Dict[str, Any]] = []

        if "playerzero" in q_lower:
            results = [
                {
                    "title": "PlayerZero Launch: AI Debugging & Product Quality Platform",
                    "link": "https://x.com/PlayerZeroApp/status/1900123456789012345",
                    "snippet": "We are excited to announce PlayerZero's official launch! Huge thanks to @sama and @packyM for the early support. #DevTools #LaunchDay",
                    "position": 1
                },
                {
                    "title": "Why debugging is changing forever - LinkedIn Post by Elena Verna",
                    "link": "https://www.linkedin.com/posts/elenaverna_devquality-ai-debugging-activity-7170012345678901234",
                    "snippet": "Just tried @PlayerZeroApp. The developer experience is game changing. Coordinated launch rollout across tech leads today.",
                    "position": 2
                },
                {
                    "title": "Social Capital Inc. Client Showcase: PlayerZero Launch Blitz",
                    "link": "https://sociallcapital.com/work/playerzero",
                    "snippet": "PlayerZero engaged Social Capital for their March 2026 launch orchestration across X and tech community leaders.",
                    "position": 3
                }
            ]
        elif "wispr flow" in q_lower or "wispr" in q_lower:
            results = [
                {
                    "title": "Wispr Flow: Voice-First Dictation for Developers",
                    "link": "https://x.com/WisprFlow/status/1890123456789012345",
                    "snippet": "Wispr Flow is live on February 12, 2026! Voice to text that types 3x faster than your keyboard. Co-announced by @swyx and @gregisenberg.",
                    "position": 1
                },
                {
                    "title": "Wispr Flow Launch Breakdown - LinkedIn Post by Jason Lemkin",
                    "link": "https://www.linkedin.com/posts/jasonmlemkin_saas-voice-ai-activity-7160012345678901234",
                    "snippet": "Wispr Flow dropped their launch on Feb 14, 2026. Notice the 3-day multi-creator testimonial wave across engineering influencers.",
                    "position": 2
                }
            ]
        elif "poly ai" in q_lower or "poly" in q_lower:
            results = [
                {
                    "title": "PolyAI Conversational Assistant Enterprise Launch",
                    "link": "https://x.com/PolyAI_LLM/status/1895123456789012345",
                    "snippet": "Announcing our next-gen enterprise voice agents. Shout out to @packyM and @swyx for joining our launch day discussion space.",
                    "position": 1
                },
                {
                    "title": "LinkedIn: Poly AI Voice Experience Revolution",
                    "link": "https://www.linkedin.com/posts/polyai_enterpriseai-cx-activity-7165012345678901234",
                    "snippet": "February 2026 marks our enterprise milestone. Coordinated post campaign featuring 15 customer case studies.",
                    "position": 2
                }
            ]
        elif "airwallex" in q_lower:
            results = [
                {
                    "title": "Airwallex Global Financial Infrastructure Update",
                    "link": "https://x.com/airwallex/status/1865123456789012345",
                    "snippet": "December 2025 launch: Borderless cards and Treasury automation. Early thoughts shared by @fintech_junkie.",
                    "position": 1
                },
                {
                    "title": "Airwallex December Campaign Blitz",
                    "link": "https://www.linkedin.com/posts/airwallex_fintech-globalpayments-activity-7140012345678901234",
                    "snippet": "High-impact narrative rollout over 48 hours with tier-1 fintech founders.",
                    "position": 2
                }
            ]
        elif "gamma" in q_lower:
            results = [
                {
                    "title": "Gamma 2.0: AI Presentations & Documents Launch",
                    "link": "https://x.com/heygemma/status/1855123456789012345",
                    "snippet": "Launched in November 2025! Over 100 creators posted interactive decks within a 4-hour synchronized launch window.",
                    "position": 1
                },
                {
                    "title": "Gamma Viral Loop Anatomy - LinkedIn",
                    "link": "https://www.linkedin.com/posts/gammaapp_presentations-growth-activity-7130012345678901234",
                    "snippet": "Case study on Gamma's November 2025 blitz: template seeding across Notion and design influencers.",
                    "position": 2
                }
            ]
        elif "cartesia" in q_lower:
            results = [
                {
                    "title": "Cartesia Sonic Voice Model Launch",
                    "link": "https://x.com/cartesia_ai/status/1845123456789012345",
                    "snippet": "October 2025: Sub-100ms conversational audio is here. Retweeted and tested live by @swyx and @gregisenberg.",
                    "position": 1
                }
            ]
        elif "deel" in q_lower:
            results = [
                {
                    "title": "Deel HR & Global Payroll Expansion Blitz",
                    "link": "https://x.com/deel/status/1842123456789012345",
                    "snippet": "October 2025: Deel rolls out full-stack talent compliance. Coordinated thread drop across international HR leaders.",
                    "position": 1
                }
            ]
        elif "superblocks" in q_lower:
            results = [
                {
                    "title": "Superblocks AI Copilot for Internal Tools",
                    "link": "https://x.com/superblocks/status/1790123456789012345",
                    "snippet": "May 2025: Build internal dashboards in minutes with AI. Launch wave supported by developer advocates across X.",
                    "position": 1
                }
            ]
        elif "icon" in q_lower:
            results = [
                {
                    "title": "Icon 3D Printed Architecture Series Launch",
                    "link": "https://x.com/Icon3DTech/status/1755123456789012345",
                    "snippet": "February 2025: Next-generation robotic construction unveil. Video demos syndicated across architectural influencers.",
                    "position": 1
                }
            ]
        else:
            results = [
                {
                    "title": f"Search result for {query}",
                    "link": "https://example.com/search-result",
                    "snippet": f"Relevant coverage and background discussion for query: {query}.",
                    "position": 1
                }
            ]

        return {"query": query, "results": results[:num_results]}

    def _mock_news_search(self, query: str) -> Dict[str, Any]:
        """Realistic mock news results."""
        q_lower = query.lower()
        results: List[Dict[str, Any]] = []

        if "playerzero" in q_lower:
            results = [
                {
                    "title": "PlayerZero Emerges with AI-Driven Engineering Quality Platform",
                    "link": "https://techcrunch.com/2026/03/05/playerzero-launch",
                    "snippet": "San Francisco-based PlayerZero announces official product launch in March 2026.",
                    "date": "2026-03-05",
                    "source": "TechCrunch"
                }
            ]
        elif "wispr" in q_lower:
            results = [
                {
                    "title": "Wispr Flow Debuts Neural Voice Dictation for Mac",
                    "link": "https://venturebeat.com/2026/02/12/wispr-flow-launch",
                    "snippet": "Wispr Flow announced its public launch on February 12, 2026, targeting developers and writers.",
                    "date": "2026-02-12",
                    "source": "VentureBeat"
                }
            ]
        elif "cartesia" in q_lower:
            results = [
                {
                    "title": "Cartesia Debuts Ultra-Fast Realtime Audio Generation",
                    "link": "https://techcrunch.com/2025/10/18/cartesia-sonic-launch",
                    "snippet": "Cartesia launched its flagship Sonic voice model on October 18, 2025.",
                    "date": "2025-10-18",
                    "source": "TechCrunch"
                }
            ]
        elif "gamma" in q_lower:
            results = [
                {
                    "title": "Gamma Celebrates 2.0 Launch with Viral Visual Storytelling Tools",
                    "link": "https://forbes.com/sites/innovation/2025/11/10/gamma-ai-docs-launch",
                    "snippet": "Gamma rolled out their major product release in November 2025.",
                    "date": "2025-11-10",
                    "source": "Forbes"
                }
            ]
        else:
            results = [
                {
                    "title": f"Industry Press Coverage: {query}",
                    "link": "https://news.example.com/coverage",
                    "snippet": f"Recent coverage and press statements regarding {query}.",
                    "date": "2025-06-01",
                    "source": "Industry Wire"
                }
            ]

        return {"query": query, "results": results}
