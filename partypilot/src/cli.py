"""
PartyPilot CLI
==============
A simple "agent skill" style command-line interface: a single command that
invokes the full multi-agent planning pipeline and pretty-prints the result.
This is the primary way a user (or another agent/orchestrator) interacts with
PartyPilot without needing to know anything about its internal architecture.

Usage:
    python -m src.cli plan --occasion "30th birthday" --guests 20 --budget 500 \
        --style outdoor --dietary vegetarian,gluten-free --guest-names alice,bob,carol
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agents.coordinator import CoordinatorAgent, PlanRequest


def main():
    parser = argparse.ArgumentParser(prog="partypilot", description="PartyPilot multi-agent event planner")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_cmd = sub.add_parser("plan", help="Generate a full event plan")
    plan_cmd.add_argument("--occasion", required=True, help="e.g. '30th birthday', 'wedding'")
    plan_cmd.add_argument("--guests", type=int, required=True, help="Expected guest count")
    plan_cmd.add_argument("--budget", type=float, required=True, help="Total budget")
    plan_cmd.add_argument("--style", default="any", choices=["indoor", "outdoor", "any"])
    plan_cmd.add_argument("--dietary", default="", help="Comma-separated dietary needs, e.g. vegan,gluten-free")
    plan_cmd.add_argument("--start-time", default="6:00 PM")
    plan_cmd.add_argument("--guest-names", default="", help="Comma-separated guest names (optional)")
    plan_cmd.add_argument("--json", action="store_true", help="Output raw JSON instead of pretty print")

    args = parser.parse_args()

    if args.command == "plan":
        coordinator = CoordinatorAgent()
        request = PlanRequest(
            occasion=args.occasion,
            guest_count=args.guests,
            total_budget=args.budget,
            style=args.style,
            dietary_needs=args.dietary,
            start_time=args.start_time,
        )
        guest_names = [n.strip() for n in args.guest_names.split(",") if n.strip()]
        result = coordinator.plan_event(request, guest_names=guest_names)

        if args.json:
            print(json.dumps(result, indent=2))
            return

        if not result["ok"]:
            print(f"❌ Planning failed at stage '{result['stage']}': {result['error']}")
            sys.exit(1)

        _pretty_print(result)


def _pretty_print(result: dict):
    print("=" * 60)
    print(f"🎉 PARTY PLAN: {result['occasion'].title()}")
    print("=" * 60)
    print(f"Guests: {result['guest_count']}")
    gl = result["guest_list_summary"]
    if gl.get("total_invited", 0) > 0:
        print(f"  Invited so far: {gl['total_invited']} (confirmed: {gl['confirmed']}, "
              f"pending: {gl['pending']}, declined: {gl['declined']})")
        if gl.get("dietary_tags"):
            print(f"  Dietary tags on file: {', '.join(gl['dietary_tags'])}")

    print("\n💰 BUDGET")
    br = result["budget_report"]
    print(f"  Total budget: ${br['total_budget']:.2f}")
    for cat, alloc in br["allocation"].items():
        spent = br["spent"].get(cat, 0)
        print(f"  - {cat.title():15s} allocated ${alloc:8.2f}  spent ${spent:8.2f}")
    print(f"  Remaining: ${br['remaining']:.2f}" + ("  ⚠️ OVER BUDGET" if br["over_budget"] else ""))

    print("\n📍 RECOMMENDED VENUE")
    v = result["recommended_venue"]
    if v:
        print(f"  {v['name']} ({v['type']}, capacity {v['capacity']}) - ${v['price_per_person']}/person")
        print(f"  Features: {', '.join(v['features'])}")
    else:
        print("  No venue found matching constraints -- consider raising budget or guest count flexibility.")

    print("\n🍽️  RECOMMENDED CATERER")
    c = result["recommended_caterer"]
    if c:
        print(f"  {c['name']} ({c['cuisine']}) - ${c['price_per_person']}/person")
        print(f"  Dietary options: {', '.join(c['dietary_options'])}")
    else:
        print("  No caterer found matching constraints -- consider raising budget or relaxing dietary filters.")

    print("\n🕒 TIMELINE")
    for step in result["timeline"]:
        print(f"  {step['start']} - {step['end']}   {step['activity']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
