"""Findings cache and state storage.

Maintains findings.json to prevent re-spending API credits across runs.
Supports saving per-client findings, retrieving raw tool_results, and checking cached clients.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FindingsStore:
    """Manages flat JSON storage of client investigation findings and tool evidence."""

    def __init__(self, filepath: Optional[str] = "findings.json"):
        self.filepath = filepath
        self._data: Dict[str, Any] = {
            "metadata": {
                "version": "1.0",
                "agency": "Social Capital Inc.",
            },
            "clients": {},
            "synthesis": None
        }
        if self.filepath and self.filepath != ":memory:":
            self.load()

    def load(self) -> None:
        """Load findings from disk if file exists."""
        if not self.filepath or self.filepath == ":memory:":
            return
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self._data.update(loaded)
            except Exception as e:
                logger.error(f"Failed to read cache {self.filepath}: {e}")

    def save(self) -> None:
        """Persist findings to disk."""
        if not self.filepath or self.filepath == ":memory:":
            return
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write cache {self.filepath}: {e}")

    def has_client(self, client_name: str) -> bool:
        """Check if client has an existing finding."""
        client_entry = self._data.get("clients", {}).get(client_name)
        if not client_entry:
            return False
        # Ensure it has a non-empty summary or finding
        return bool(client_entry.get("summary") or client_entry.get("turns"))

    def get_client(self, client_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve finding for a specific client."""
        return self._data.get("clients", {}).get(client_name)

    def save_client_finding(self, client_name: str, finding_data: Dict[str, Any]) -> None:
        """Save finding for a client and persist immediately."""
        if "clients" not in self._data:
            self._data["clients"] = {}
        self._data["clients"][client_name] = finding_data
        self.save()

    def save_synthesis(self, synthesis_text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save overall synthesis output."""
        self._data["synthesis"] = {
            "text": synthesis_text,
            "metadata": metadata or {}
        }
        self.save()

    def get_synthesis(self) -> Optional[Dict[str, Any]]:
        """Retrieve saved synthesis."""
        return self._data.get("synthesis")

    def set_mode(self, mode: str, metadata_updates: Optional[Dict[str, Any]] = None) -> None:
        """Stamp whether run was 'live' or 'mock' and save metadata."""
        if "metadata" not in self._data:
            self._data["metadata"] = {}
        self._data["metadata"]["mode"] = mode
        if metadata_updates:
            self._data["metadata"].update(metadata_updates)
        self.save()

    def save_audit_ledger(self, ledger_claims: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
        """Store verified/unverified claims ledger and score in findings.json."""
        self._data["ledger"] = {
            "claims": ledger_claims,
            "stats": stats
        }
        self.save()

    def clear_clients(self) -> None:
        """Reset client findings, synthesis, and ledger for a fresh run."""
        self._data["clients"] = {}
        self._data["synthesis"] = None
        self._data["ledger"] = None
        self.save()

    def get_all_findings(self) -> Dict[str, Any]:
        """Return all client findings."""
        return dict(self._data.get("clients", {}))

    def get_all_raw_tool_results(self) -> List[Dict[str, Any]]:
        """Gather all raw tool results across all stored client runs."""
        all_results: List[Dict[str, Any]] = []
        for client_name, client_data in self._data.get("clients", {}).items():
            tool_results = client_data.get("tool_results", [])
            for res in tool_results:
                enriched = dict(res)
                enriched["_client"] = client_name
                all_results.append(enriched)
        return all_results
