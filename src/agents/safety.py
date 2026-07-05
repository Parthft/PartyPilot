"""
Safety / Guardrail layer for PartyPilot.

Every agent runs its inputs and outputs through these checks before acting.
This is intentionally simple and dependency-free so it's easy to audit --
the point for this capstone is to demonstrate *deliberate, visible* security
practices, not to build a production-grade moderation stack.

Guardrails implemented:
1. Input validation (types, ranges) -- prevents malformed/malicious tool args.
2. Budget sanity checks -- refuses to proceed on nonsensical budgets.
3. PII minimization -- guest contact info is never sent to external tools or
   logged; only aggregate counts/dietary tags are used by planning agents.
4. Prompt-injection guard -- strips/flags suspicious instructions embedded in
   free-text fields (e.g. guest notes) before they reach any LLM call.
5. No secrets in code -- API keys are read from environment variables only,
   never hardcoded (see .env.example).
"""

import re
from dataclasses import dataclass

# Patterns that suggest an embedded prompt-injection attempt inside free text
# (e.g. a "guest note" field trying to hijack the agent's instructions).
_INJECTION_PATTERNS = [
    r"ignore (all|previous|the) instructions",
    r"system prompt",
    r"you are now",
    r"disregard (all|previous)",
    r"act as (an? )?(unfiltered|jailbroken)",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


@dataclass
class GuardrailResult:
    ok: bool
    reason: str = ""
    sanitized_value: object = None


def validate_guest_count(value) -> GuardrailResult:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return GuardrailResult(False, "Guest count must be a whole number.")
    if n <= 0:
        return GuardrailResult(False, "Guest count must be positive.")
    if n > 5000:
        return GuardrailResult(False, "Guest count exceeds supported planning range (5000).")
    return GuardrailResult(True, sanitized_value=n)


def validate_budget(value, name: str = "Budget") -> GuardrailResult:
    try:
        b = float(value)
    except (TypeError, ValueError):
        return GuardrailResult(False, f"{name} must be a number.")
    if b < 0:
        return GuardrailResult(False, f"{name} cannot be negative.")
    if b > 10_000_000:
        return GuardrailResult(False, f"{name} exceeds supported planning range.")
    return GuardrailResult(True, sanitized_value=b)


def sanitize_free_text(text: str) -> GuardrailResult:
    """Flags free-text fields (guest notes, occasion descriptions) that look
    like prompt-injection attempts, and strips control characters."""
    if text is None:
        return GuardrailResult(True, sanitized_value="")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text)).strip()
    if _INJECTION_RE.search(cleaned):
        return GuardrailResult(
            False,
            "Free-text field flagged for a suspicious instruction-like pattern "
            "and was not passed to any downstream agent.",
        )
    return GuardrailResult(True, sanitized_value=cleaned)


def redact_pii_for_logs(guest: dict) -> dict:
    """Returns a copy of a guest record safe for logging/telemetry: drops
    phone/email/address, keeps only planning-relevant fields."""
    allowed_keys = {"name_initial", "dietary_tags", "rsvp_status"}
    safe = {}
    if "name" in guest and guest["name"]:
        safe["name_initial"] = str(guest["name"])[0].upper() + "."
    for k in ("dietary_tags", "rsvp_status"):
        if k in guest:
            safe[k] = guest[k]
    return {k: v for k, v in safe.items() if k in allowed_keys or True}
