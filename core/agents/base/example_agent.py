"""
Example Agent Implementation

This module provides a concrete example of how to implement an agent
using the BaseAgent framework. It demonstrates best practices for
agent development in the LiMOS system.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from .agent import BaseAgent, AgentCapability, AgentConfig
from .config import config_manager
from ..memory.memory import AgentMemory, FileBackend


class EchoAgent(BaseAgent):
    """
    Example agent that echoes input with processing.

    This agent demonstrates:
    - Basic agent lifecycle
    - Memory usage
    - Claude API integration
    - Error handling
    - Configuration management
    """

    def __init__(self, config: AgentConfig, anthropic_client: Optional[Anthropic] = None):
        """Initialize the echo agent."""
        super().__init__(config, anthropic_client)
        self.memory: Optional[AgentMemory] = None
        self.processed_count = 0

    async def _initialize(self) -> None:
        """Initialize agent-specific resources."""
        # Set up persistent memory
        storage_path = f"storage/agents/{self.agent_id}/memory"
        backend = FileBackend(storage_path)
        self.memory = AgentMemory(self.agent_id, backend)

        # Load previous state if exists
        self.processed_count = await self.memory.get("processed_count", 0)

        # Set up system memory
        self.set_memory("initialization_time", "utcnow()")
        self.set_memory("agent_type", "EchoAgent")

        print(f"EchoAgent {self.name} initialized successfully")

    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the echo processing."""
        # Extract input text
        text = input_data.get("text", "")
        if not text:
            raise ValueError("Input 'text' is required")

        # Store input in memory for history
        await self.memory.set(
            f"input_{self.processed_count}",
            text,
            ttl_seconds=3600,  # Keep for 1 hour
            tags=["input", "history"]
        )

        # Process with Claude if available and requested
        enhanced_text = text
        if self.anthropic_client and kwargs.get("enhance", False):
            enhanced_text = await self._enhance_with_claude(text)

        # Create response
        response = {
            "original_text": text,
            "enhanced_text": enhanced_text,
            "processed_at": "utcnow()",
            "agent_id": self.agent_id,
            "processing_count": self.processed_count + 1,
            "memory_stats": await self.memory.get_stats()
        }

        # Update counters
        self.processed_count += 1
        await self.memory.set("processed_count", self.processed_count)

        # Store result in memory
        await self.memory.set(
            f"result_{self.processed_count}",
            response,
            ttl_seconds=7200,  # Keep for 2 hours
            tags=["output", "history"]
        )

        return response

    async def _enhance_with_claude(self, text: str) -> str:
        """Enhance text using Claude API."""
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"Please enhance and improve this text while keeping its core meaning: {text}"
                }]
            )
            return response.content[0].text
        except Exception as e:
            # Fallback to original text if enhancement fails
            print(f"Text enhancement failed: {e}")
            return text

    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        if self.memory:
            # Clean up old entries (older than 24 hours)
            await self.memory.cleanup_expired()
            print(f"EchoAgent {self.name} cleaned up successfully")

    async def get_processing_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent processing history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent processing results
        """
        if not self.memory:
            return []

        history = []
        results = await self.memory.find_by_tags(["output"])

        # Sort by processing count (reverse order for most recent first)
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get("processing_count", 0),
            reverse=True
        )

        return [result for _, result in sorted_results[:limit]]

    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics."""
        base_stats = self.get_status_info()

        custom_stats = {
            "processed_count": self.processed_count,
            "memory_stats": await self.memory.get_stats() if self.memory else {},
            "recent_history_count": len(await self.get_processing_history()),
        }

        return {**base_stats, **custom_stats}


async def create_echo_agent(
    name: str = "EchoAgent",
    environment: str = "development",
    **config_overrides
) -> EchoAgent:
    """
    Factory function to create a configured EchoAgent.

    Args:
        name: Agent name
        environment: Environment configuration to use
        **config_overrides: Additional configuration parameters

    Returns:
        Configured and initialized EchoAgent instance
    """
    # Create configuration
    config = config_manager.create_agent_config(
        name=name,
        description="Example agent that processes and echoes text input",
        capabilities=[
            AgentCapability.TEXT_PROCESSING,
            AgentCapability.API_INTEGRATION
        ],
        environment=environment,
        **config_overrides
    )

    # Create agent
    agent = EchoAgent(config)

    # Initialize
    await agent.initialize()

    return agent


async def demo_echo_agent():
    """Demonstrate EchoAgent functionality."""
    print("Creating EchoAgent...")

    # Create agent
    agent = await create_echo_agent("DemoEcho")

    try:
        print(f"Agent created: {agent}")
        print(f"Status: {agent.status}")

        # Test basic processing
        print("\n--- Basic Processing ---")
        result1 = await agent.execute({
            "text": "Hello, this is a test message for the echo agent."
        })
        print(f"Result: {json.dumps(result1, indent=2, default=str)}")

        # Test enhanced processing (if Claude API is available)
        print("\n--- Enhanced Processing ---")
        result2 = await agent.execute({
            "text": "The quick brown fox jumps over the lazy dog."
        }, enhance=True)
        print(f"Enhanced result: {json.dumps(result2, indent=2, default=str)}")

        # Show processing history
        print("\n--- Processing History ---")
        history = await agent.get_processing_history(limit=5)
        print(f"History entries: {len(history)}")
        for i, entry in enumerate(history):
            print(f"  {i+1}. Count: {entry.get('processing_count', 'N/A')}")

        # Show agent stats
        print("\n--- Agent Statistics ---")
        stats = await agent.get_agent_stats()
        print(f"Total processed: {stats['processed_count']}")
        print(f"Memory entries: {stats['memory_stats'].get('total_entries', 0)}")

    finally:
        # Clean up
        await agent.cleanup()
        print(f"\nAgent cleaned up. Final status: {agent.status}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_echo_agent())