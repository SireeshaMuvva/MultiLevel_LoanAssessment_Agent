# mcp_server/test_mcp_server.py
# Task 3.3 — Test that MCP server starts and tools are discoverable
# This simulates how your agents will connect to the MCP server.
#
# Run: python -m mcp_server.test_mcp_server

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """
    Connects to the MCP server as a client and:
    1. Lists all available tools
    2. Calls two tools directly via MCP protocol
    This is exactly what LangGraph agents do when they use MCP tools.
    """

    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.server"],
        env=None
    )

    print("\n🔌 Connecting to MCP Server via stdio transport...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Step 1: Initialise the session
            await session.initialize()
            print("✅ MCP Session initialised successfully\n")

            # Step 2: List all registered tools
            tools_response = await session.list_tools()
            tools = tools_response.tools

            print(f"📋 Tools registered on MCP server: {len(tools)}")
            for tool in tools:
                print(f"   → {tool.name}")
                print(f"      {tool.description[:80]}...")

            # Step 3: Call Tool 4 — calculate_emi via MCP
            print("\n" + "="*60)
            print("TEST: Calling tool_calculate_emi via MCP protocol")
            print("="*60)

            emi_result = await session.call_tool(
                "tool_calculate_emi",
                arguments={
                    "principal": 4500000.0,
                    "annual_interest_rate": 8.5,
                    "tenure_years": 20
                }
            )
            print(f"✅ EMI Tool Response:")
            print(f"   {emi_result.content[0].text[:300]}")

            # Step 4: Call Tool 1 — get_credit_score via MCP
            print("\n" + "="*60)
            print("TEST: Calling tool_get_credit_score via MCP protocol")
            print("="*60)

            credit_result = await session.call_tool(
                "tool_get_credit_score",
                arguments={"pan_number": "ABCDE1234F"}
            )
            print(f"✅ Credit Score Tool Response:")
            print(f"   {credit_result.content[0].text[:300]}")

    print("\n✅ MCP Server test complete!")
    print("   Your tools are correctly exposed via MCP protocol.")
    print("   Ready for Week 4 — Building Agents!\n")


if __name__ == "__main__":
    print("\n🏦 Loan Eligibility Agent — MCP Server Test")
    asyncio.run(test_mcp_server())