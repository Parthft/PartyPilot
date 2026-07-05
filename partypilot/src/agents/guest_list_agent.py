"""
Guest List Agent
================
Owns the invite list: tracks names, RSVP status, and dietary/allergy tags.

Design note on privacy: this agent is the *only* place raw guest PII (names)
lives. Every other agent (Budget, Logistics, Coordinator) only ever receives
aggregate counts and dietary tags -- never names or contact info. This keeps
sensitive personal data local and minimizes what could leak through logs or
downstream tool calls (see agents/safety.py::redact_pii_for_logs).
"""

from dataclasses import dataclass, field

from .safety import sanitize_free_text, validate_guest_count


@dataclass
class Guest:
    name: str
    rsvp_status: str = "pending"  # pending | yes | no
    dietary_tags: list = field(default_factory=list)


class GuestListAgent:
    name = "GuestListAgent"

    def __init__(self):
        self._guests: list[Guest] = []

    def add_guest(self, name: str, dietary_tags: list[str] | None = None) -> dict:
        clean = sanitize_free_text(name)
        if not clean.ok:
            return {"ok": False, "error": clean.reason}
        guest = Guest(name=clean.sanitized_value, dietary_tags=dietary_tags or [])
        self._guests.append(guest)
        return {"ok": True, "guest_count": len(self._guests)}

    def bulk_add(self, names: list[str]) -> dict:
        for n in names:
            self.add_guest(n)
        return {"ok": True, "guest_count": len(self._guests)}

    def set_rsvp(self, name: str, status: str) -> dict:
        status = status.lower().strip()
        if status not in ("pending", "yes", "no"):
            return {"ok": False, "error": "RSVP status must be pending, yes, or no."}
        for g in self._guests:
            if g.name.lower() == name.lower():
                g.rsvp_status = status
                return {"ok": True}
        return {"ok": False, "error": f"Guest '{name}' not found."}

    def summary(self, expected_count: int | None = None) -> dict:
        """Returns an aggregate, PII-free summary for other agents to consume."""
        if expected_count is not None:
            check = validate_guest_count(expected_count)
            if not check.ok:
                return {"ok": False, "error": check.reason}

        confirmed = sum(1 for g in self._guests if g.rsvp_status == "yes")
        declined = sum(1 for g in self._guests if g.rsvp_status == "no")
        pending = sum(1 for g in self._guests if g.rsvp_status == "pending")
        all_tags = sorted({tag for g in self._guests for tag in g.dietary_tags})

        return {
            "ok": True,
            "total_invited": len(self._guests),
            "confirmed": confirmed,
            "declined": declined,
            "pending": pending,
            "dietary_tags": all_tags,
        }
