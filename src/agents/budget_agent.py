"""
Budget Agent
============
Allocates a total budget across planning categories using simple, transparent
heuristics, and tracks running spend as the Logistics Agent selects real
venues/caterers. Kept rule-based (not an LLM call) deliberately -- arithmetic
should be deterministic and auditable, not "vibed."
"""

from .safety import validate_budget, validate_guest_count

# Default allocation percentages; tunable per occasion type.
DEFAULT_ALLOCATION = {
    "venue": 0.35,
    "catering": 0.40,
    "decor": 0.10,
    "entertainment": 0.10,
    "contingency": 0.05,
}


class BudgetAgent:
    name = "BudgetAgent"

    def __init__(self, total_budget: float, guest_count: int):
        b_check = validate_budget(total_budget)
        g_check = validate_guest_count(guest_count)
        if not b_check.ok:
            raise ValueError(b_check.reason)
        if not g_check.ok:
            raise ValueError(g_check.reason)

        self.total_budget = b_check.sanitized_value
        self.guest_count = g_check.sanitized_value
        self.allocation = {
            k: round(self.total_budget * pct, 2) for k, pct in DEFAULT_ALLOCATION.items()
        }
        self.spent = {k: 0.0 for k in self.allocation}

    def per_person(self, category: str) -> float:
        if category not in self.allocation:
            raise ValueError(f"Unknown category: {category}")
        return round(self.allocation[category] / self.guest_count, 2)

    def record_spend(self, category: str, amount: float) -> dict:
        if category not in self.allocation:
            return {"ok": False, "error": f"Unknown category: {category}"}
        check = validate_budget(amount, "amount")
        if not check.ok:
            return {"ok": False, "error": check.reason}
        self.spent[category] += check.sanitized_value
        remaining = self.allocation[category] - self.spent[category]
        return {
            "ok": True,
            "category": category,
            "spent": round(self.spent[category], 2),
            "allocated": self.allocation[category],
            "remaining": round(remaining, 2),
            "over_budget": remaining < 0,
        }

    def full_report(self) -> dict:
        total_spent = sum(self.spent.values())
        return {
            "ok": True,
            "total_budget": self.total_budget,
            "allocation": self.allocation,
            "spent": {k: round(v, 2) for k, v in self.spent.items()},
            "total_spent": round(total_spent, 2),
            "remaining": round(self.total_budget - total_spent, 2),
            "over_budget": total_spent > self.total_budget,
        }
