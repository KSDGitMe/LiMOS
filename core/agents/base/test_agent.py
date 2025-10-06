"""
Tests for BaseAgent class and related components.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from .agent import (
    AgentCapability,
    AgentConfig,
    AgentContext,
    AgentMetrics,
    AgentStatus,
    BaseAgent
)
from .config import AgentConfigLoader, EnvironmentConfig
from ..memory.memory import AgentMemory, InMemoryBackend
from ..registry.registry import AgentRegistry


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing purposes."""

    def __init__(self, config: AgentConfig, fail_init: bool = False, fail_execute: bool = False):
        super().__init__(config)
        self.fail_init = fail_init
        self.fail_execute = fail_execute
        self.init_called = False
        self.execute_called = False
        self.cleanup_called = False

    async def _initialize(self) -> None:
        """Test initialization."""
        self.init_called = True
        if self.fail_init:
            raise RuntimeError("Initialization failed")

    async def _execute(self, input_data: dict, **kwargs) -> dict:
        """Test execution."""
        self.execute_called = True
        if self.fail_execute:
            raise RuntimeError("Execution failed")
        return {"result": "success", "input": input_data, "kwargs": kwargs}

    async def _cleanup(self) -> None:
        """Test cleanup."""
        self.cleanup_called = True


@pytest.fixture
def sample_config():
    """Create a sample agent configuration."""
    return AgentConfig(
        name="TestAgent",
        description="A test agent",
        capabilities=[AgentCapability.TEXT_PROCESSING],
        max_turns=5,
        timeout_seconds=10
    )


@pytest.fixture
def test_agent(sample_config):
    """Create a test agent instance."""
    return TestAgent(sample_config)


class TestAgentConfig:
    """Test AgentConfig model."""

    def test_config_creation(self):
        """Test creating agent configuration."""
        config = AgentConfig(
            name="TestAgent",
            description="A test agent",
            capabilities=[AgentCapability.TEXT_PROCESSING, AgentCapability.IMAGE_ANALYSIS]
        )

        assert config.name == "TestAgent"
        assert config.description == "A test agent"
        assert len(config.capabilities) == 2
        assert config.max_turns == 10  # default
        assert config.timeout_seconds == 300  # default

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        config = AgentConfig(
            name="Valid",
            description="Valid agent",
            capabilities=[AgentCapability.TEXT_PROCESSING]
        )
        assert config.name == "Valid"

        # Test defaults
        assert config.version == "1.0.0"
        assert config.environment == "development"
        assert config.debug is False


class TestBaseAgent:
    """Test BaseAgent functionality."""

    def test_agent_creation(self, sample_config):
        """Test agent creation."""
        agent = TestAgent(sample_config)
        assert agent.name == "TestAgent"
        assert agent.status == AgentStatus.IDLE
        assert not agent.is_initialized
        assert agent.agent_id == sample_config.agent_id

    def test_config_validation_failure(self):
        """Test agent creation with invalid config."""
        # Invalid max_turns
        with pytest.raises(ValueError, match="max_turns must be positive"):
            invalid_config = AgentConfig(
                name="Invalid",
                description="Invalid agent",
                capabilities=[AgentCapability.TEXT_PROCESSING],
                max_turns=0
            )
            TestAgent(invalid_config)

        # Invalid timeout
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            invalid_config = AgentConfig(
                name="Invalid",
                description="Invalid agent",
                capabilities=[AgentCapability.TEXT_PROCESSING],
                timeout_seconds=-1
            )
            TestAgent(invalid_config)

    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_agent):
        """Test agent initialization."""
        assert not test_agent.is_initialized
        assert test_agent.status == AgentStatus.IDLE

        await test_agent.initialize()

        assert test_agent.is_initialized
        assert test_agent.init_called
        assert test_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_agent_initialization_failure(self, sample_config):
        """Test agent initialization failure."""
        agent = TestAgent(sample_config, fail_init=True)

        with pytest.raises(RuntimeError, match="Failed to initialize agent"):
            await agent.initialize()

        assert not agent.is_initialized
        assert agent.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_agent_execution(self, test_agent):
        """Test agent execution."""
        input_data = {"test": "data"}

        result = await test_agent.execute(input_data, extra_param="value")

        assert test_agent.is_initialized
        assert test_agent.execute_called
        assert result["result"] == "success"
        assert result["input"] == input_data
        assert result["kwargs"]["extra_param"] == "value"
        assert test_agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_agent_execution_failure(self, sample_config):
        """Test agent execution failure."""
        agent = TestAgent(sample_config, fail_execute=True)

        with pytest.raises(RuntimeError, match="Agent execution failed"):
            await agent.execute({"test": "data"})

        assert agent.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_agent_execution_timeout(self, sample_config):
        """Test agent execution timeout."""
        # Create agent with very short timeout
        config = AgentConfig(
            name="TimeoutAgent",
            description="Agent that times out",
            capabilities=[AgentCapability.TEXT_PROCESSING],
            timeout_seconds=1
        )

        class SlowAgent(TestAgent):
            async def _execute(self, input_data: dict, **kwargs) -> dict:
                await asyncio.sleep(2)  # Sleep longer than timeout
                return {"result": "should not reach here"}

        agent = SlowAgent(config)

        with pytest.raises(TimeoutError, match="Agent execution timed out"):
            await agent.execute({"test": "data"})

        assert agent.status == AgentStatus.ERROR

    @pytest.mark.asyncio
    async def test_agent_memory(self, test_agent):
        """Test agent memory operations."""
        # Set memory
        test_agent.set_memory("key1", "value1")
        test_agent.set_memory("key2", {"nested": "data"})

        # Get memory
        assert test_agent.get_memory("key1") == "value1"
        assert test_agent.get_memory("key2") == {"nested": "data"}
        assert test_agent.get_memory("nonexistent", "default") == "default"

        # Check memory property
        memory = test_agent.memory
        assert "key1" in memory
        assert "key2" in memory

        # Clear memory
        test_agent.clear_memory()
        assert test_agent.get_memory("key1") is None

    @pytest.mark.asyncio
    async def test_agent_metrics(self, test_agent):
        """Test agent metrics tracking."""
        # Initial metrics
        assert test_agent.metrics.total_executions == 0
        assert test_agent.metrics.successful_executions == 0
        assert test_agent.metrics.failed_executions == 0

        # Successful execution
        await test_agent.execute({"test": "data"})
        assert test_agent.metrics.total_executions == 1
        assert test_agent.metrics.successful_executions == 1
        assert test_agent.metrics.failed_executions == 0
        assert test_agent.metrics.last_execution is not None

    @pytest.mark.asyncio
    async def test_context_history(self, test_agent):
        """Test context history tracking."""
        # Execute multiple times
        await test_agent.execute({"test": "data1"})
        await test_agent.execute({"test": "data2"})

        # Check history
        history = test_agent.get_context_history()
        assert len(history) == 2
        assert history[0].input_data == {"test": "data2"}  # Most recent first
        assert history[1].input_data == {"test": "data1"}

        # Check limited history
        limited_history = test_agent.get_context_history(limit=1)
        assert len(limited_history) == 1
        assert limited_history[0].input_data == {"test": "data2"}

    @pytest.mark.asyncio
    async def test_agent_cleanup(self, test_agent):
        """Test agent cleanup."""
        await test_agent.initialize()
        await test_agent.cleanup()

        assert test_agent.cleanup_called
        assert test_agent.status == AgentStatus.STOPPED
        assert not test_agent.is_initialized

    def test_agent_status_info(self, test_agent):
        """Test agent status information."""
        status_info = test_agent.get_status_info()

        assert status_info["agent_id"] == test_agent.agent_id
        assert status_info["name"] == test_agent.name
        assert status_info["status"] == AgentStatus.IDLE
        assert "config" in status_info
        assert "metrics" in status_info

    def test_agent_repr(self, test_agent):
        """Test agent string representation."""
        repr_str = repr(test_agent)
        assert "TestAgent" in repr_str
        assert test_agent.agent_id in repr_str
        assert test_agent.name in repr_str


class TestAgentMemory:
    """Test AgentMemory functionality."""

    @pytest.fixture
    def agent_memory(self):
        """Create an agent memory instance."""
        return AgentMemory("test-agent", InMemoryBackend())

    @pytest.mark.asyncio
    async def test_memory_operations(self, agent_memory):
        """Test basic memory operations."""
        # Set and get
        await agent_memory.set("key1", "value1")
        value = await agent_memory.get("key1")
        assert value == "value1"

        # Default value
        value = await agent_memory.get("nonexistent", "default")
        assert value == "default"

        # Exists check
        assert await agent_memory.exists("key1")
        assert not await agent_memory.exists("nonexistent")

        # Delete
        assert await agent_memory.delete("key1")
        assert not await agent_memory.exists("key1")
        assert not await agent_memory.delete("key1")  # Already deleted

    @pytest.mark.asyncio
    async def test_memory_ttl(self, agent_memory):
        """Test memory TTL functionality."""
        # Set with TTL
        await agent_memory.set("temp_key", "temp_value", ttl_seconds=1)
        assert await agent_memory.exists("temp_key")

        # Wait for expiration
        await asyncio.sleep(1.1)
        assert not await agent_memory.exists("temp_key")

    @pytest.mark.asyncio
    async def test_memory_tags(self, agent_memory):
        """Test memory tags functionality."""
        await agent_memory.set("key1", "value1", tags=["tag1", "tag2"])
        await agent_memory.set("key2", "value2", tags=["tag2", "tag3"])
        await agent_memory.set("key3", "value3", tags=["tag1"])

        # Find by tags
        results = await agent_memory.find_by_tags(["tag1"])
        assert len(results) == 2
        assert "key1" in results
        assert "key3" in results

    @pytest.mark.asyncio
    async def test_memory_keys_listing(self, agent_memory):
        """Test memory keys listing."""
        await agent_memory.set("prefix_key1", "value1")
        await agent_memory.set("prefix_key2", "value2")
        await agent_memory.set("other_key", "value3")

        # All keys
        all_keys = await agent_memory.keys()
        assert len(all_keys) == 3

        # Pattern matching
        prefix_keys = await agent_memory.keys("prefix_*")
        assert len(prefix_keys) == 2

    @pytest.mark.asyncio
    async def test_memory_stats(self, agent_memory):
        """Test memory statistics."""
        await agent_memory.set("key1", "value1", tags=["tag1"])
        await agent_memory.set("key2", "value2", ttl_seconds=1)

        stats = await agent_memory.get_stats()
        assert stats["agent_id"] == "test-agent"
        assert stats["total_entries"] == 2
        assert "tag_distribution" in stats


class TestAgentRegistry:
    """Test AgentRegistry functionality."""

    @pytest.fixture
    def registry(self):
        """Create a fresh agent registry."""
        return AgentRegistry()

    @pytest.mark.asyncio
    async def test_agent_registration(self, registry, sample_config):
        """Test agent registration."""
        agent = TestAgent(sample_config)

        # Register agent
        agent_id = await registry.register_agent(agent, tags={"test"}, metadata={"version": "1.0"})
        assert agent_id == agent.agent_id

        # Get agent
        retrieved_agent = registry.get_agent(agent_id)
        assert retrieved_agent is agent

        # Get registration
        registration = registry.get_registration(agent_id)
        assert registration is not None
        assert registration.name == agent.name
        assert "test" in registration.tags

    @pytest.mark.asyncio
    async def test_agent_class_registration(self, registry):
        """Test agent class registration."""
        await registry.register_agent_class(TestAgent, "CustomTestAgent")

        # Create agent using registry
        config = AgentConfig(
            name="RegistryCreated",
            description="Created via registry",
            capabilities=[AgentCapability.TEXT_PROCESSING]
        )

        agent = await registry.create_agent("CustomTestAgent", config)
        assert isinstance(agent, TestAgent)
        assert agent.name == "RegistryCreated"

    @pytest.mark.asyncio
    async def test_agent_listing(self, registry, sample_config):
        """Test agent listing with filters."""
        # Register multiple agents
        agent1 = TestAgent(sample_config)
        agent2 = TestAgent(AgentConfig(
            name="Agent2",
            description="Second agent",
            capabilities=[AgentCapability.IMAGE_ANALYSIS]
        ))

        await registry.register_agent(agent1, tags={"test", "group1"})
        await registry.register_agent(agent2, tags={"test", "group2"})

        # List all agents
        all_agents = registry.list_agents()
        assert len(all_agents) == 2

        # Filter by tags
        group1_agents = registry.list_agents(tags={"group1"})
        assert len(group1_agents) == 1
        assert group1_agents[0].name == "TestAgent"

        # Filter by capabilities
        text_agents = registry.list_agents(capabilities=["text_processing"])
        assert len(text_agents) == 1

    @pytest.mark.asyncio
    async def test_registry_stats(self, registry, sample_config):
        """Test registry statistics."""
        agent = TestAgent(sample_config)
        await registry.register_agent(agent, tags={"test"})

        stats = registry.get_registry_stats()
        assert stats["total_agents"] == 1
        assert stats["status_distribution"]["idle"] == 1
        assert stats["tag_distribution"]["test"] == 1


if __name__ == "__main__":
    pytest.main([__file__])