# PartyPilot — 5-Minute Video Script

**Goal:** hit every scored element (problem, why agents, architecture, demo, the build) inside 5 minutes. Aim for ~4:30 to leave buffer.

---

### 0:00–0:40 — Problem Statement (talking head or slide)
> "Planning any event — a birthday, a family get-together, a small wedding — means juggling a guest list, a budget you don't want to blow, hours of venue and caterer research across a dozen tabs, and a timeline that has to actually work on the day. It's tedious and error-prone — somebody always forgets that Aunt Carol is vegan until the caterer's already booked. I built PartyPilot to fix that: describe your event in one sentence, get a complete, budget-aware plan back in seconds."

### 0:40–1:30 — Why Agents (slide: the 4-box diagram)
> "This isn't a job for one chatbot response. It's really four different problems: tracking guests and RSVPs, doing exact budget math, searching vendors against constraints, and building a schedule. So PartyPilot splits these into four specialized agents coordinated by a router. That means budget math is deterministic instead of 'vibed' by an LLM, and — importantly — guest names only ever live in one place instead of leaking through every step."

### 1:30–2:45 — Architecture (show `docs/architecture.svg`)
> "The Coordinator Agent is the only entry point — it validates the request through a security/guardrail layer, then routes to three specialists: the Guest List Agent, which is the only place PII lives; the Budget Agent, which is rule-based on purpose; and the Logistics Agent, which searches venues and caterers. Those searches go through a real MCP server I built — `search_venues` and `search_caterers` — served over the actual Model Context Protocol, not just regular function calls. I can prove that: [switch to terminal]"

*(Screen recording: run `python scripts/test_mcp_client.py`, show it listing tools and calling them over a real client/server session.)*

> "That's a real MCP client talking to a real MCP server over stdio."

### 2:45–4:00 — Live Demo (screen recording)
*(Run the CLI command live)*
```
python -m src.cli plan --occasion "30th birthday" --guests 20 --budget 500 \
  --style outdoor --dietary vegetarian --guest-names "Alice,Bob,Carol,Dave"
```
> "One sentence in, and I get back: a budget broken down by category with actual spend against it, a venue and caterer that both fit that budget, and a full timeline. Now let's look at security — this matters because this agent handles real personal information."

*(Run the 3 guardrail test cases: negative budget, prompt injection, absurd guest count — show each cleanly rejected.)*

> "Negative budget — rejected. Someone trying to inject 'ignore all previous instructions' into the occasion field — caught and blocked before it reaches any agent. An unrealistic guest count — rejected with a clear reason, not a crash."

### 4:00–4:30 — The Build
> "This is built in Python with the official MCP SDK for the tool server, no external API keys required to run — it ships with realistic mock venue and caterer data so anyone can try it immediately, and it's structured so swapping that mock data for a live Places API later is a one-file change. Full code, README, and setup instructions are linked below."

### 4:30 — Close
> "That's PartyPilot — four agents, one real MCP server, and a party plan in seconds. Thanks for watching."

---

**Recording checklist:**
- [ ] Screen recording of `python scripts/test_mcp_client.py` output
- [ ] Screen recording of the CLI demo command + full output
- [ ] Screen recording of the 3 guardrail rejection tests
- [ ] Slide or on-screen `docs/architecture.svg` during the architecture section
- [ ] Upload unlisted/public to YouTube, keep under 5:00
