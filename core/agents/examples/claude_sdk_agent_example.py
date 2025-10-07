#!/usr/bin/env python3
"""
Example Agent using Official Claude Agent SDK

This demonstrates how to build an agent using the official claude-agent-sdk
package from Anthropic. This SDK is designed for integration with Claude Code
and provides built-in tool management and conversation handling.

Installation:
    pip install claude-agent-sdk

Key Features:
    - Official Anthropic SDK
    - Built-in tool discovery
    - Async/await support
    - MCP (Model Context Protocol) integration
    - Designed for Claude Code CLI
"""

import asyncio
from typing import Any, Dict
from claude_agent_sdk import tool, query, ClaudeSDKClient, ClaudeAgentOptions


# Define tools using the @tool decorator
@tool(
    "calculate_fuel_cost",
    "Calculate the total fuel cost based on gallons and price per gallon",
    {"gallons": float, "price_per_gallon": float}
)
async def calculate_fuel_cost(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate total fuel cost.

    The tool decorator requires:
    1. name: string identifier
    2. description: what the tool does
    3. input_schema: dict mapping parameter names to types

    Returns must be in the format:
    {"content": [{"type": "text", "text": "result"}]}
    """
    gallons = args["gallons"]
    price = args["price_per_gallon"]
    total = gallons * price

    return {
        "content": [
            {
                "type": "text",
                "text": f"Total fuel cost: ${total:.2f} ({gallons} gallons @ ${price:.2f}/gallon)"
            }
        ]
    }


@tool(
    "calculate_mpg",
    "Calculate miles per gallon given miles driven and gallons used",
    {"miles": float, "gallons": float}
)
async def calculate_mpg(args: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate fuel efficiency in MPG."""
    miles = args["miles"]
    gallons = args["gallons"]

    if gallons == 0:
        return {
            "content": [
                {"type": "text", "text": "Error: Cannot divide by zero gallons"}
            ]
        }

    mpg = miles / gallons

    return {
        "content": [
            {
                "type": "text",
                "text": f"Fuel efficiency: {mpg:.2f} MPG ({miles} miles / {gallons} gallons)"
            }
        ]
    }


@tool(
    "get_vehicle_info",
    "Get information about a vehicle by VIN",
    {"vin": str}
)
async def get_vehicle_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve vehicle information (mock data for demo)."""
    vin = args["vin"]

    # In a real implementation, this would query a database
    mock_data = {
        "vin": vin,
        "make": "Honda",
        "model": "Civic",
        "year": 2020,
        "mileage": 45000
    }

    return {
        "content": [
            {
                "type": "text",
                "text": f"Vehicle Info:\n"
                       f"  VIN: {mock_data['vin']}\n"
                       f"  Make: {mock_data['make']}\n"
                       f"  Model: {mock_data['model']}\n"
                       f"  Year: {mock_data['year']}\n"
                       f"  Mileage: {mock_data['mileage']:,}"
            }
        ]
    }


class FleetAgentSDK:
    """
    Example Fleet Agent using Claude Agent SDK.

    This class wraps the Claude SDK client and provides a clean interface
    for agent operations. It demonstrates best practices for using the
    official SDK.

    Note: Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self):
        """
        Initialize the Fleet Agent with Claude SDK.

        The API key is read from the ANTHROPIC_API_KEY environment variable.
        """
        self.options = ClaudeAgentOptions(
            system_prompt="""You are a fleet management assistant. You help with:
            - Calculating fuel costs and efficiency
            - Vehicle information lookup
            - Cost analysis and reporting

            Use the available tools to perform calculations and retrieve data.
            Be precise with numerical calculations and provide clear explanations.""",
            allowed_tools=["calculate_fuel_cost", "calculate_mpg", "get_vehicle_info"]
        )

        self.client = None

    async def initialize(self):
        """Initialize the Claude SDK client."""
        try:
            self.client = ClaudeSDKClient(options=self.options)
            print("✅ Fleet Agent SDK initialized")
        except Exception as e:
            print(f"⚠️  SDK initialization demo (requires ANTHROPIC_API_KEY): {e}")

    async def query(self, message: str) -> str:
        """
        Send a query to the agent and get a response.

        Args:
            message: User message/query

        Returns:
            Agent's response text
        """
        if not self.client:
            await self.initialize()

        # Use the query function with the client
        response = await query(message)
        return response

    async def cleanup(self):
        """Clean up resources."""
        # SDK handles cleanup automatically
        print("✅ Fleet Agent SDK cleaned up")


async def demo_basic_usage():
    """Demonstrate basic usage of Claude Agent SDK tools."""
    print("=" * 70)
    print("Claude Agent SDK - Tool Definition Demo")
    print("=" * 70)

    print("\nClaude Agent SDK tools are defined with the @tool decorator:")
    print("  - Name: Identifier for the tool")
    print("  - Description: What the tool does")
    print("  - Schema: Input parameter types")
    print()
    print("Tools defined:")
    print("  ✅ calculate_fuel_cost - Calculate total fuel cost")
    print("  ✅ calculate_mpg - Calculate miles per gallon")
    print("  ✅ get_vehicle_info - Get vehicle information")
    print()
    print("These tools are automatically discovered and invoked by Claude")
    print("when using the ClaudeSDKClient with an API key.")


async def demo_agent_usage():
    """Demonstrate using the agent with Claude SDK client."""
    print("\n" + "=" * 70)
    print("Claude Agent SDK - Agent Client Demo")
    print("=" * 70)

    print("\nNote: This requires ANTHROPIC_API_KEY environment variable.")
    print("The agent will use the @tool decorated functions automatically.")
    print("This demo shows the structure - actual API calls require a valid key.")

    # Create agent instance
    agent = FleetAgentSDK()
    await agent.initialize()

    # Example queries (would need valid API key to execute)
    example_queries = [
        "Calculate the cost of 15 gallons at $3.50 per gallon",
        "What's the MPG if I drove 400 miles and used 14 gallons?",
        "Look up vehicle information for VIN 1HGCM82633A123456"
    ]

    print("\nExample queries the agent can handle:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")

    await agent.cleanup()


async def main():
    """Run all demonstrations."""
    print("\n🚀 Claude Agent SDK Examples\n")

    # Demo 1: Direct tool usage
    await demo_basic_usage()

    # Demo 2: Agent client usage
    await demo_agent_usage()

    print("\n" + "=" * 70)
    print("✅ All demonstrations completed!")
    print("=" * 70)

    print("\nKey Takeaways:")
    print("  1. @tool decorator defines callable functions for Claude")
    print("  2. Tools must return: {'content': [{'type': 'text', 'text': '...'}]}")
    print("  3. ClaudeSDKClient manages conversations and tool invocation")
    print("  4. All operations are async/await")
    print("  5. Requires ANTHROPIC_API_KEY for actual API calls")


if __name__ == "__main__":
    asyncio.run(main())
