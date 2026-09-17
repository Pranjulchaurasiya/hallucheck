"""Seed client data for Social Capital Inc. launches.

Scraped from sociallcapital.com/work:
9 known product launches with their launch months.
"""

from typing import List, Dict

CLIENTS: List[Dict[str, str]] = [
    {"name": "PlayerZero", "launch_month": "2026-03"},
    {"name": "Wispr Flow", "launch_month": "2026-02"},
    {"name": "Poly AI", "launch_month": "2026-02"},
    {"name": "Airwallex", "launch_month": "2025-12"},
    {"name": "Gamma", "launch_month": "2025-11"},
    {"name": "Cartesia", "launch_month": "2025-10"},
    {"name": "Deel", "launch_month": "2025-10"},
    {"name": "Superblocks", "launch_month": "2025-05"},
    {"name": "Icon", "launch_month": "2025-02"},
]


def get_clients() -> List[Dict[str, str]]:
    """Return a copy of the 9 seed clients."""
    return [dict(c) for c in CLIENTS]
