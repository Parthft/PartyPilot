"""
Logistics Agent
===============
Finds venues + caterers that fit the budget/guest constraints, and builds a
day-of timeline. It uses the exact same tool logic exposed by our MCP server
(src/mcp_server/server.py::search_venues / search_caterers) -- imported
directly here for fast, dependency-free demo execution.

For a live demonstration of real MCP client<->server protocol communication
(stdio transport), see `scripts/test_mcp_client.py`, which drives the same
tools through an actual MCP client session. Both paths call identical
business logic, so behavior is guaranteed consistent.
"""

import json
import sys
from pathlib import Path

# Reuse the MCP server's tool logic directly (same data, same validation).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp_server.server import search_venues as _search_venues_tool
from mcp_server.server import search_caterers as _search_caterers_tool


class LogisticsAgent:
    name = "LogisticsAgent"

    def find_venue_options(self, guest_count: int, budget_per_person: float, style: str = "any") -> dict:
        raw = _search_venues_tool(guest_count, budget_per_person, style)
        return json.loads(raw)

    def find_caterer_options(self, guest_count: int, budget_per_person: float, dietary_needs: str = "") -> dict:
        raw = _search_caterers_tool(guest_count, budget_per_person, dietary_needs)
        return json.loads(raw)

    def build_timeline(self, occasion: str, start_time: str = "6:00 PM") -> list[dict]:
        """Simple heuristic timeline generator based on occasion type."""
        occasion_lower = (occasion or "").lower()
        if "wedding" in occasion_lower:
            steps = [
                ("Guest arrival & welcome drinks", 30),
                ("Ceremony", 30),
                ("Cocktail hour", 60),
                ("Dinner service", 60),
                ("Speeches & toasts", 30),
                ("First dance & open floor", 90),
                ("Cake cutting", 15),
                ("Farewell", 15),
            ]
        elif "birthday" in occasion_lower:
            steps = [
                ("Guest arrival", 30),
                ("Icebreaker / mingling", 30),
                ("Food service", 45),
                ("Cake & candles", 15),
                ("Games / entertainment", 60),
                ("Open dance floor / social time", 60),
                ("Wind down & thank-yous", 20),
            ]
        else:
            steps = [
                ("Guest arrival", 20),
                ("Welcome & introductions", 15),
                ("Food service", 45),
                ("Main activity / entertainment", 60),
                ("Closing remarks", 15),
            ]

        from datetime import datetime, timedelta
        try:
            current = datetime.strptime(start_time, "%I:%M %p")
        except ValueError:
            current = datetime.strptime("6:00 PM", "%I:%M %p")

        timeline = []
        for label, minutes in steps:
            end = current + timedelta(minutes=minutes)
            timeline.append({
                "activity": label,
                "start": current.strftime("%I:%M %p"),
                "end": end.strftime("%I:%M %p"),
            })
            current = end
        return timeline
