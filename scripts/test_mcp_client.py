"""
Demonstrates real MCP client <-> server communication (stdio transport)
against src/mcp_server/server.py. Run this to prove the planning tools are
genuinely served over the Model Context Protocol, not just imported as
regular Python functions.

Usage:
    python scripts/test_mcp_client.py
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "src", "mcp_server", "server.py")


async def main():
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools exposed by PartyPilot MCP server:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description.strip().splitlines()[0]}")

            print("\nCalling search_venues(guest_count=20, budget_per_person=15, style='outdoor')...")
            result = await session.call_tool(
                "search_venues",
                arguments={"guest_count": 20, "budget_per_person": 15, "style": "outdoor"},
            )
            print(result.content[0].text)

            print("\nCalling search_caterers(guest_count=20, budget_per_person=15, dietary_needs='vegetarian')...")
            result = await session.call_tool(
                "search_caterers",
                arguments={"guest_count": 20, "budget_per_person": 15, "dietary_needs": "vegetarian"},
            )
            print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
