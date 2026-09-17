"""Deterministic grounding validator for synthesis and investigation claims.

Validates specific claims (handles, dates, URLs) against the corpus of raw tool results
without any LLM calls. Tags unverified claims and computes a grounding score.
"""

import re
import json
import logging
from typing import Dict, Any, List, Set, Tuple, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GroundingValidator:
    """100% deterministic validator verifying claims against raw search/news evidence."""

    def __init__(self, raw_tool_results: List[Dict[str, Any]]):
        self.raw_tool_results = raw_tool_results
        self.corpus_text = ""
        self.corpus_urls: Set[str] = set()
        self.corpus_handles: Set[str] = set()
        self._build_corpus()

    def _build_corpus(self) -> None:
        """Flatten raw tool results into a searchable corpus and index known entities."""
        corpus_parts: List[str] = []

        for item in self.raw_tool_results:
            result_obj = item.get("result", {})
            results_list = result_obj.get("results", []) if isinstance(result_obj, dict) else []

            for r in results_list:
                title = r.get("title", "")
                link = r.get("link", "")
                snippet = r.get("snippet", "")
                date = r.get("date", "")
                source = r.get("source", "")

                text_block = f"{title} {link} {snippet} {date} {source}".strip()
                corpus_parts.append(text_block)

                # Index URLs
                if link:
                    clean_link = link.strip().rstrip("/").lower()
                    self.corpus_urls.add(clean_link)
                    parsed = urlparse(clean_link)
                    self.corpus_urls.add(parsed.netloc + parsed.path)

                # Extract handles from corpus text
                found_handles = re.findall(r"@([A-Za-z0-9_]+)", text_block)
                for h in found_handles:
                    self.corpus_handles.add(h.lower())

                # Also extract handles embedded in URLs (e.g. x.com/username)
                url_handles = re.findall(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]+)", text_block, re.I)
                for uh in url_handles:
                    if uh.lower() not in {"status", "search", "home", "intent", "i"}:
                        self.corpus_handles.add(uh.lower())

        self.corpus_text = " \n ".join(corpus_parts).lower()

    def extract_handles(self, text: str) -> List[str]:
        """Extract unique @handles from text."""
        raw_matches = re.findall(r"@([A-Za-z0-9_]+)", text)
        seen = set()
        unique_handles = []
        for h in raw_matches:
            if h.lower() not in seen:
                seen.add(h.lower())
                unique_handles.append(h)
        return unique_handles

    def extract_urls(self, text: str) -> List[str]:
        """Extract unique http/https URLs from text."""
        matches = re.findall(r"https?://[^\s)\]\">]+", text)
        seen = set()
        unique_urls = []
        for u in matches:
            cleaned = u.rstrip(".,;!?:")
            if cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                unique_urls.append(cleaned)
        return unique_urls

    def extract_dates(self, text: str) -> List[str]:
        """Extract explicit calendar dates and month-year timestamps from text."""
        date_patterns = [
            # e.g. February 12, 2026 or February 12 2026
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            # e.g. 2026-03-05 or 2025-10-18
            r"\b\d{4}-\d{2}-\d{2}\b",
            # e.g. March 2026 or November 2025
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
        ]
        found = []
        seen = set()
        for p in date_patterns:
            matches = re.findall(p, text, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if clean_m.lower() not in seen:
                    seen.add(clean_m.lower())
                    found.append(clean_m)
        return found

    def verify_handle(self, handle: str) -> Tuple[bool, Optional[str]]:
        """Verify if a Twitter/X handle appears in raw evidence."""
        h_clean = handle.lstrip("@").lower()
        if h_clean in self.corpus_handles or f"@{h_clean}" in self.corpus_text or f"/{h_clean}" in self.corpus_text:
            return True, f"Found handle @{handle.lstrip('@')} in retrieved tool results"
        return False, f"Handle @{handle.lstrip('@')} not found in any retrieved search or news results"

    def verify_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """Verify if a URL appears in raw evidence."""
        clean_url = url.rstrip("/").lower()
        if clean_url in self.corpus_urls:
            return True, f"Exact URL found in raw tool results: {url}"
        
        parsed = urlparse(clean_url)
        path_repr = (parsed.netloc + parsed.path).lower()
        if path_repr in self.corpus_urls or path_repr in self.corpus_text:
            return True, f"URL path found in evidence: {url}"

        return False, f"URL not found in any retrieved search or news results: {url}"

    def verify_date(self, date_str: str) -> Tuple[bool, Optional[str]]:
        """Verify if a date reference is grounded in raw evidence."""
        clean_date = date_str.lower()
        if clean_date in self.corpus_text:
            return True, f"Date reference '{date_str}' corroborated by raw snippets"

        # Check ISO format e.g. "2026-03" for "March 2026"
        month_map = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12"
        }
        for month_name, mm in month_map.items():
            if month_name in clean_date:
                # Extract year
                year_match = re.search(r"\b(20\d\d)\b", clean_date)
                if year_match:
                    iso_prefix = f"{year_match.group(1)}-{mm}"
                    if iso_prefix in self.corpus_text:
                        return True, f"Date reference corroborated via date timestamp ({iso_prefix})"

        return False, f"Date reference '{date_str}' not corroborated in raw tool results"

    def audit_text(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive grounding audit on a text block (e.g. synthesis or findings).

        Returns:
            Dictionary containing verified claims, unverified claims, score, and annotated text.
        """
        handles = self.extract_handles(text)
        urls = self.extract_urls(text)
        dates = self.extract_dates(text)

        verified_claims: List[Dict[str, str]] = []
        unverified_claims: List[Dict[str, str]] = []

        # Check handles
        for h in handles:
            is_valid, reason = self.verify_handle(h)
            claim_info = {"type": "creator_handle", "claim": f"@{h.lstrip('@')}", "detail": reason or ""}
            if is_valid:
                verified_claims.append(claim_info)
            else:
                unverified_claims.append(claim_info)

        # Check URLs
        for u in urls:
            is_valid, reason = self.verify_url(u)
            claim_info = {"type": "url_citation", "claim": u, "detail": reason or ""}
            if is_valid:
                verified_claims.append(claim_info)
            else:
                unverified_claims.append(claim_info)

        # Check Dates
        for d in dates:
            is_valid, reason = self.verify_date(d)
            claim_info = {"type": "launch_date", "claim": d, "detail": reason or ""}
            if is_valid:
                verified_claims.append(claim_info)
            else:
                unverified_claims.append(claim_info)

        total_claims = len(verified_claims) + len(unverified_claims)
        grounding_score = (len(verified_claims) / total_claims * 100.0) if total_claims > 0 else 100.0

        # Annotate text: append badge next to unverified claims
        annotated_text = text
        for unv in unverified_claims:
            claim_str = unv["claim"]
            # Replace occurrences with tagged version if not already tagged
            if "[UNVERIFIED" not in claim_str:
                pattern = re.escape(claim_str) + r"(?!\w)"
                annotated_text = re.sub(
                    f"({pattern})(?!\\s*\\[UNVERIFIED)",
                    r"\1 **[UNVERIFIED]**",
                    annotated_text
                )

        return {
            "total_claims": total_claims,
            "verified_count": len(verified_claims),
            "unverified_count": len(unverified_claims),
            "grounding_score_percent": round(grounding_score, 1),
            "verified_claims": verified_claims,
            "unverified_claims": unverified_claims,
            "annotated_text": annotated_text
        }


def format_markdown_report(
    synthesis_audit: Dict[str, Any],
    client_findings: Dict[str, Any],
    budget_stats: Dict[str, int]
) -> str:
    """Generate final report.md cleanly separating verified and unverified claims."""
    score = synthesis_audit["grounding_score_percent"]
    verified_list = synthesis_audit["verified_claims"]
    unverified_list = synthesis_audit["unverified_claims"]

    lines: List[str] = [
        "# Social Capital Inc. Launch-Pattern Investigation & Grounding Report",
        "",
        "> **Deterministic Verification Status**: "
        f"Grounding Score: **{score}%** | "
        f"Verified Claims: **{len(verified_list)}** | "
        f"Unverified Claims: **{len(unverified_list)}** | "
        f"Tool Calls Used: **{budget_stats.get('used', 0)} / {budget_stats.get('max', 60)}**",
        "",
        "---",
        "",
        "## 1. Executive Synthesis (Cross-Launch Patterns)",
        "",
        synthesis_audit["annotated_text"],
        "",
        "---",
        "",
        "## 2. Grounding & Verification Audit Ledger",
        "",
        "Deterministic check matching every named handle, date, and URL against raw Serper search/news API results.",
        "",
        "### ✅ Verified Claims (Corroborated by Raw Tool Results)",
        ""
    ]

    if verified_list:
        lines.append("| Type | Claim | Corroboration Details |")
        lines.append("|---|---|---|")
        for c in verified_list:
            lines.append(f"| `{c['type']}` | **{c['claim']}** | {c['detail']} |")
    else:
        lines.append("*No verifiable claims detected.*")

    lines.extend([
        "",
        "### ⚠️ Unverified Claims (Flagged - Not Found in Retrieved Results)",
        ""
    ])

    if unverified_list:
        lines.append("> [!WARNING]")
        lines.append("> The following entities were asserted in the report but could NOT be traced to raw search/news results. They are marked **[UNVERIFIED]** to prevent hallucinated conclusions.")
        lines.append("")
        lines.append("| Type | Claim | Issue / Reason |")
        lines.append("|---|---|---|")
        for c in unverified_list:
            lines.append(f"| `{c['type']}` | **{c['claim']}** | {c['detail']} |")
    else:
        lines.append("🎉 **Zero hallucinations detected.** All cited handles, dates, and URLs were grounded in raw search/news data.")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Client Investigation Summaries",
        ""
    ])

    for client_name, data in client_findings.items():
        launch = data.get("launch_month", "Unknown")
        status = data.get("status", "completed")
        turns = data.get("turns_taken", 0)
        tool_count = len(data.get("tool_results", []))
        summary = data.get("summary", "No summary available.")

        status_badge = "✅ Complete" if status == "completed" else "⚠️ Incomplete (Max turns reached)"
        lines.extend([
            f"### {client_name}",
            f"- **Target Launch Month**: {launch}",
            f"- **Investigation Status**: {status_badge} ({turns} turns, {tool_count} tool queries)",
            "",
            summary,
            ""
        ])

    lines.extend([
        "---",
        "",
        "## 4. Run Metadata & Guardrail Statistics",
        f"- **Global Tool Calls Consumed**: {budget_stats.get('used', 0)} / {budget_stats.get('max', 60)}",
        f"- **Remaining Budget**: {budget_stats.get('remaining', 0)}",
        f"- **Clients Investigated**: {len(client_findings)}",
        f"- **Grounding Pass Rate**: {score}%",
        ""
    ])

    return "\n".join(lines)
