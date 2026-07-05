# PartyPilot: A Multi-Agent Concierge That Plans Your Event From One Sentence
### Track: Concierge Agents

## The Problem

Planning an event — a birthday, a family reunion, a small wedding — is death by a thousand small decisions. You're juggling a guest list and RSVPs, trying not to blow a budget, researching venues and caterers across a dozen browser tabs, and building a timeline that doesn't fall apart by 8pm. Nobody remembers Aunt Carol is vegan until the caterer's already booked. It's the kind of task that's high-stakes for the host and completely uninteresting to automate with a single chatbot response — which is exactly why it's a great fit for agents.

## Why Agents

A single LLM call can *describe* a party plan, but it can't reliably do arithmetic on a budget, keep a growing guest list consistent across turns, or guarantee it never leaks a guest's name into a vendor search. PartyPilot splits the problem into four cooperating agents, each with a narrow, auditable job:

- **Coordinator Agent** — the only entry point. Validates the request through a guardrail layer, routes to specialists, assembles the final plan. It never does domain work itself.
- **Guest List Agent** — the *only* agent that ever touches guest names. Tracks RSVP status and dietary tags, and exposes only an aggregate, PII-free summary (counts + tags) to everyone else.
- **Budget Agent** — deterministic, rule-based budget allocation across venue/catering/decor/entertainment/contingency, and running spend tracking. Kept intentionally non-LLM: budget math should be exact, not "vibed."
- **Logistics Agent** — searches venues and caterers against guest count, budget, and dietary constraints, and builds a day-of timeline. It calls out to an actual **MCP server**.

This separation means each agent is small enough to test in isolation, and sensitive data (names) never has to travel further than one hop.

## Architecture & MCP Integration

`src/mcp_server/server.py` exposes two tools — `search_venues` and `search_caterers` — over the real Model Context Protocol (stdio transport), using the official `mcp` Python SDK. This isn't a "pretend" MCP wrapper: `scripts/test_mcp_client.py` spins up an actual MCP client session against the server, calls `list_tools()`, and invokes both tools over the wire, proving the tools are genuinely served via MCP and could be plugged into any MCP-compatible client (Claude Desktop, an ADK-based agent, etc.) with zero changes.

The Logistics Agent, for fast local execution, calls the same tool functions directly — the business logic is identical either way, so behavior is guaranteed consistent between the "fast path" and the "real protocol path."

*(See `docs/architecture.svg` for the full diagram.)*

## Security Features

Every agent runs inputs through a shared guardrail module (`src/agents/safety.py`):

1. **Input validation** — guest counts and budgets are type- and range-checked before any agent logic runs (rejects negative budgets, absurd guest counts, non-numeric input).
2. **Prompt-injection detection** — free-text fields (like the occasion description) are scanned for instruction-hijacking patterns (e.g. "ignore all previous instructions") before being passed to any downstream logic.
3. **PII minimization** — guest names live only inside the Guest List Agent; every other agent, and every external tool call, only ever sees aggregate counts and dietary tags.
4. **No hardcoded secrets** — the project runs with zero API keys out of the box (mock data); `.env.example` documents the *optional* keys for a future real-API integration, and `.gitignore` excludes any real `.env`.

These aren't theoretical — they're demonstrated live with three failing-on-purpose test cases in the video and in the README (negative budget, injected instruction, 99-million-guest party all get cleanly rejected with a clear reason, not a crash).

## Demo Walkthrough

Input:
```
python -m src.cli plan --occasion "30th birthday" --guests 20 --budget 500 \
  --style outdoor --dietary vegetarian --guest-names "Alice,Bob,Carol,Dave"
```

Output: a full plan — allocated and spent budget per category, a recommended venue and caterer that both fit the actual per-person budget after allocation, and a minute-by-minute timeline built around the occasion type (birthday vs. wedding vs. generic event get different timeline shapes).

## What We'd Add With More Time

- Swap the bundled mock venue/caterer datasets for a live Places API and real caterer directories.
- Natural-language request parsing via an LLM (Gemini) so hosts can type "help me plan my sister's baby shower" instead of using CLI flags.
- A lightweight web UI over the same Coordinator — the agents are already UI-agnostic.
- Persistent guest lists/RSVPs across sessions (currently in-memory per run for simplicity).

## Why This Matters

The judges explicitly called out "managing the invite list for a party" as an example of the kind of everyday-life problem this track is looking for. PartyPilot takes that seriously: it's not a toy demo, it's a genuinely useful, testable, extensible multi-agent system — the guardrails are real, the MCP integration is real, and the whole thing runs in seconds with zero API keys required to try it.

---
*Word count target: ~750 words (well under the 2,500 word limit — leaves room to expand with screenshots/results if desired before final submission).*
