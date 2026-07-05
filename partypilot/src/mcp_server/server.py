"""
PartyPilot MCP Server
======================
Exposes venue and catering search as MCP (Model Context Protocol) tools so that
any MCP-compatible agent/client (including the Logistics Agent in this project)
can query real-time-style planning data through a standard tool interface.

Run standalone for testing:
    python src/mcp_server/server.py

This uses the official `mcp` Python SDK (stdio transport) so it can be plugged
into any MCP client (Claude Desktop, an ADK agent, etc.) with zero code changes
on the client side beyond pointing it at this script.

NOTE ON SECURITY:
- No API keys, secrets, or PII are hardcoded here.
- All inputs are validated (see `_validate_positive_int` / `_validate_budget`)
  before being used, to guard against malformed or malicious tool calls.
"""

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

mcp = FastMCP("partypilot-planning-tools")


def _load_json(filename: str) -> list[dict[str, Any]]:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_positive_int(value: int, name: str) -> int:
    """Guardrail: reject negative/absurd values before they hit business logic."""
    if not isinstance(value, int) or value <= 0 or value > 100_000:
        raise ValueError(f"Invalid {name}: must be a positive integer, got {value!r}")
    return value


def _validate_budget(value: float, name: str = "budget") -> float:
    if not isinstance(value, (int, float)) or value < 0 or value > 10_000_000:
        raise ValueError(f"Invalid {name}: must be a non-negative number, got {value!r}")
    return float(value)


@mcp.tool()
def search_venues(guest_count: int, budget_per_person: float, style: str = "any") -> str:
    """
    Search available venues that can host the given guest count within the
    per-person budget. Optionally filter by style ("indoor", "outdoor", "any").

    Args:
        guest_count: number of guests expected to attend.
        budget_per_person: maximum amount (in currency units) willing to spend
            on venue cost per guest.
        style: "indoor", "outdoor", or "any".
    """
    guest_count = _validate_positive_int(guest_count, "guest_count")
    budget_per_person = _validate_budget(budget_per_person, "budget_per_person")
    style = style.lower().strip() if style else "any"
    if style not in ("indoor", "outdoor", "any"):
        style = "any"

    venues = _load_json("venues.json")
    matches = [
        v for v in venues
        if v["capacity"] >= guest_count
        and v["price_per_person"] <= budget_per_person
        and (style == "any" or v["type"] == style)
    ]
    matches.sort(key=lambda v: v["price_per_person"])
    return json.dumps({"query": {"guest_count": guest_count, "budget_per_person": budget_per_person, "style": style},
                        "results": matches}, indent=2)


@mcp.tool()
def search_caterers(guest_count: int, budget_per_person: float, dietary_needs: str = "") -> str:
    """
    Search caterers that fit the budget and can accommodate given dietary needs.

    Args:
        guest_count: number of guests to cater for (used for context/logging only).
        budget_per_person: maximum spend per guest on food.
        dietary_needs: comma-separated dietary tags, e.g. "vegan,gluten-free".
    """
    guest_count = _validate_positive_int(guest_count, "guest_count")
    budget_per_person = _validate_budget(budget_per_person, "budget_per_person")
    needs = [n.strip().lower() for n in dietary_needs.split(",") if n.strip()]

    caterers = _load_json("caterers.json")
    matches = []
    for c in caterers:
        if c["price_per_person"] > budget_per_person:
            continue
        options = [o.lower() for o in c["dietary_options"]]
        if needs and not all(n in options for n in needs):
            continue
        matches.append(c)
    matches.sort(key=lambda c: c["price_per_person"])
    return json.dumps({"query": {"guest_count": guest_count, "budget_per_person": budget_per_person,
                                  "dietary_needs": needs}, "results": matches}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
