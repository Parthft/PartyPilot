"""
Coordinator Agent
=================
The entry point for a planning request. Parses the user's natural-language-ish
request into structured parameters, validates them through the guardrail
layer, then delegates to the three specialist agents and assembles their
outputs into a single, coherent party plan.

This is the "multi-agent system" backbone of PartyPilot: the Coordinator
never does domain work itself -- it only routes and assembles, which keeps
each specialist agent simple, testable, and independently replaceable.
"""

from dataclasses import dataclass

from .budget_agent import BudgetAgent
from .guest_list_agent import GuestListAgent
from .logistics_agent import LogisticsAgent
from .safety import sanitize_free_text, validate_budget, validate_guest_count


@dataclass
class PlanRequest:
    occasion: str
    guest_count: int
    total_budget: float
    style: str = "any"           # indoor | outdoor | any
    dietary_needs: str = ""      # comma-separated tags
    start_time: str = "6:00 PM"


class CoordinatorAgent:
    name = "CoordinatorAgent"

    def __init__(self):
        self.guest_list_agent = GuestListAgent()
        self.logistics_agent = LogisticsAgent()
        self.budget_agent: BudgetAgent | None = None

    def plan_event(self, request: PlanRequest, guest_names: list[str] | None = None) -> dict:
        # --- Guardrail pass: validate everything before any agent runs ---
        occasion_check = sanitize_free_text(request.occasion)
        if not occasion_check.ok:
            return {"ok": False, "stage": "input_validation", "error": occasion_check.reason}

        guest_check = validate_guest_count(request.guest_count)
        if not guest_check.ok:
            return {"ok": False, "stage": "input_validation", "error": guest_check.reason}

        budget_check = validate_budget(request.total_budget)
        if not budget_check.ok:
            return {"ok": False, "stage": "input_validation", "error": budget_check.reason}

        occasion = occasion_check.sanitized_value
        guest_count = guest_check.sanitized_value
        total_budget = budget_check.sanitized_value

        # --- Guest List Agent ---
        if guest_names:
            self.guest_list_agent.bulk_add(guest_names)
        guest_summary = self.guest_list_agent.summary(expected_count=guest_count)

        # --- Budget Agent ---
        try:
            self.budget_agent = BudgetAgent(total_budget=total_budget, guest_count=guest_count)
        except ValueError as e:
            return {"ok": False, "stage": "budget_setup", "error": str(e)}

        venue_budget_pp = self.budget_agent.per_person("venue")
        catering_budget_pp = self.budget_agent.per_person("catering")

        # --- Logistics Agent (uses MCP-served tools) ---
        venue_options = self.logistics_agent.find_venue_options(
            guest_count=guest_count, budget_per_person=venue_budget_pp, style=request.style
        )
        caterer_options = self.logistics_agent.find_caterer_options(
            guest_count=guest_count, budget_per_person=catering_budget_pp, dietary_needs=request.dietary_needs
        )
        timeline = self.logistics_agent.build_timeline(occasion, request.start_time)

        # --- Record best picks against the budget ---
        chosen_venue = venue_options["results"][0] if venue_options["results"] else None
        chosen_caterer = caterer_options["results"][0] if caterer_options["results"] else None

        if chosen_venue:
            self.budget_agent.record_spend("venue", chosen_venue["price_per_person"] * guest_count)
        if chosen_caterer:
            self.budget_agent.record_spend("catering", chosen_caterer["price_per_person"] * guest_count)

        budget_report = self.budget_agent.full_report()

        return {
            "ok": True,
            "occasion": occasion,
            "guest_count": guest_count,
            "guest_list_summary": guest_summary,
            "budget_report": budget_report,
            "recommended_venue": chosen_venue,
            "other_venue_options": venue_options["results"][1:4],
            "recommended_caterer": chosen_caterer,
            "other_caterer_options": caterer_options["results"][1:4],
            "timeline": timeline,
        }
