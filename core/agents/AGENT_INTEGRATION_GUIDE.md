# LiMOS Agent Integration Guide

This guide explains how to integrate the three available agent patterns in the LiMOS system.

## Three Agent Patterns Available

### 1. LiMOS BaseAgent Framework
**Location**: `core/agents/base/agent.py`
**Best for**: Full LiMOS integration, production agents, complex workflows
**Used by**: `receipt_agent.py`, `fleet_manager_agent.py`

### 2. Standalone Compatible Pattern
**Location**: `projects/fleet/agents/fleet_manager_agent_compatible.py`
**Best for**: Quick prototypes, independent scripts, simple agents
**Used by**: Fleet demo, standalone tools

### 3. Claude Agent SDK
**Location**: Official `claude-agent-sdk` package
**Best for**: Claude Code CLI integration, official Anthropic tooling
**Example**: `core/agents/examples/claude_sdk_agent_example.py`

---

## Pattern 1: LiMOS BaseAgent Framework

### Architecture

```python
from core.agents.base import BaseAgent, AgentConfig, AgentCapability

class MyAgent(BaseAgent):
    """Custom agent inheriting from BaseAgent."""

    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                name="MyAgent",
                description="What this agent does",
                capabilities=[AgentCapability.DATA_EXTRACTION]
            )
        super().__init__(config, **kwargs)
        # Initialize your resources

    async def _initialize(self) -> None:
        """Agent-specific initialization."""
        # Set up databases, load models, etc.
        pass

    async def _execute(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Main execution logic."""
        # Process input_data and return results
        return {"success": True, "result": "..."}

    async def _cleanup(self) -> None:
        """Clean up resources."""
        # Close connections, save state, etc.
        pass
```

### Usage

```python
import asyncio

async def main():
    # Create config
    config = AgentConfig(
        name="MyAgent",
        description="Agent description",
        capabilities=[AgentCapability.DATA_EXTRACTION],
        max_turns=10,
        timeout_seconds=300
    )

    # Initialize agent
    agent = MyAgent(config=config)
    await agent.initialize()

    # Execute
    result = await agent.execute({
        "operation": "process",
        "data": "..."
    })

    # Cleanup
    await agent.cleanup()

asyncio.run(main())
```

### Features

- ✅ Async/await throughout
- ✅ Built-in metrics and monitoring
- ✅ Lifecycle management (init, execute, cleanup)
- ✅ Status tracking
- ✅ Context history
- ✅ Memory management
- ✅ Configuration validation
- ✅ Timeout handling

### When to Use

- Building production agents
- Need metrics and monitoring
- Complex multi-step workflows
- Integration with LiMOS registry
- Require lifecycle management

---

## Pattern 2: Standalone Compatible

### Architecture

```python
from typing import Dict, Any, Callable

def tool(func: Callable) -> Callable:
    """Mark methods as agent tools."""
    func._is_tool = True
    func._tool_name = func.__name__
    return func

class BaseAgent:
    """Simple base class for tool discovery."""
    def __init__(self, name: str = "Agent"):
        self.name = name
        self.tools = self._discover_tools()

    def _discover_tools(self) -> Dict[str, Callable]:
        tools = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_is_tool'):
                tools[attr._tool_name] = attr
        return tools

class MyAgent(BaseAgent):
    """Custom agent with tools."""

    def __init__(self, name: str = "MyAgent"):
        super().__init__(name)
        # Initialize resources

    @tool
    def my_operation(self, param: str) -> Dict[str, Any]:
        """Perform an operation."""
        return {"success": True, "result": f"Processed {param}"}

    @tool
    def another_operation(self, value: float) -> Dict[str, Any]:
        """Another operation."""
        return {"success": True, "value": value * 2}
```

### Usage

```python
# Create agent
agent = MyAgent(name="TestAgent")

# Call tools directly
result = agent.my_operation("data")

# List available tools
print(agent.get_available_tools())
```

### Features

- ✅ Simple and lightweight
- ✅ Tool auto-discovery
- ✅ No async required
- ✅ Easy to understand
- ✅ Self-contained
- ✅ No external dependencies

### When to Use

- Quick prototypes
- Standalone scripts
- Simple agents
- No need for async
- Learning/teaching examples

---

## Pattern 3: Claude Agent SDK

### Architecture

```python
from claude_agent_sdk import tool, ClaudeSDKClient, ClaudeAgentOptions

# Define tools with decorator
@tool(
    "operation_name",
    "Description of what this does",
    {"param1": str, "param2": float}
)
async def my_operation(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool implementation.

    Must return: {"content": [{"type": "text", "text": "result"}]}
    """
    result = f"Processed: {args['param1']} and {args['param2']}"
    return {
        "content": [
            {"type": "text", "text": result}
        ]
    }

# Define more tools
@tool("calculate", "Perform calculation", {"x": float, "y": float})
async def calculate(args: Dict[str, Any]) -> Dict[str, Any]:
    total = args["x"] + args["y"]
    return {
        "content": [
            {"type": "text", "text": f"Result: {total}"}
        ]
    }

# Create agent client
class MyAgent:
    def __init__(self, api_key: str = None):
        self.options = ClaudeAgentOptions(
            api_key=api_key,
            system_prompt="You are a helpful assistant..."
        )
        self.client = None

    async def initialize(self):
        self.client = ClaudeSDKClient(options=self.options)

    async def query(self, message: str) -> str:
        from claude_agent_sdk import query
        return await query(message)
```

### Usage

```python
import asyncio

async def main():
    # Initialize agent
    agent = MyAgent(api_key="your_key")
    await agent.initialize()

    # Query the agent (Claude will use tools automatically)
    response = await agent.query("Calculate 5 + 10")
    print(response)

asyncio.run(main())
```

### Features

- ✅ Official Anthropic SDK
- ✅ Claude Code CLI integration
- ✅ MCP protocol support
- ✅ Automatic tool invocation
- ✅ Built-in conversation management
- ✅ Async/await

### When to Use

- Claude Code CLI integration
- Official Anthropic tooling required
- MCP server development
- Need conversation management
- Want automatic tool routing

---

## Integration Strategies

### Strategy 1: Hybrid BaseAgent + Tools

Combine LiMOS BaseAgent with tool pattern for best of both:

```python
from core.agents.base import BaseAgent, AgentConfig

def tool(func):
    func._is_tool = True
    return func

class HybridAgent(BaseAgent):
    """Agent with BaseAgent lifecycle + tool discovery."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.tools = self._discover_tools()

    def _discover_tools(self):
        tools = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '_is_tool'):
                tools[attr_name] = attr
        return tools

    async def _initialize(self):
        # BaseAgent initialization
        pass

    async def _execute(self, input_data, **kwargs):
        # Route to appropriate tool
        operation = input_data.get("operation")
        if operation in self.tools:
            return self.tools[operation](**input_data.get("params", {}))
        return {"error": "Unknown operation"}

    @tool
    def process_data(self, data: str):
        return {"result": f"Processed: {data}"}
```

### Strategy 2: Claude SDK Tool Wrapper

Wrap Claude SDK tools in BaseAgent:

```python
from core.agents.base import BaseAgent, AgentConfig
from claude_agent_sdk import tool as claude_tool

class ClaudeSDKAgent(BaseAgent):
    """BaseAgent wrapper around Claude SDK tools."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.register_claude_tools()

    def register_claude_tools(self):
        # Register Claude SDK tools
        @claude_tool("my_tool", "Description", {"param": str})
        async def my_tool(args):
            return {"content": [{"type": "text", "text": "result"}]}

        self.claude_tools = [my_tool]

    async def _execute(self, input_data, **kwargs):
        # Use Claude SDK for execution
        from claude_agent_sdk import query
        result = await query(input_data.get("query", ""))
        return {"response": result}
```

### Strategy 3: Multi-Pattern Agent Registry

Support all patterns in a unified registry:

```python
from enum import Enum
from typing import Union

class AgentType(Enum):
    BASEAGENT = "baseagent"
    STANDALONE = "standalone"
    CLAUDE_SDK = "claude_sdk"

class AgentRegistry:
    """Registry supporting all agent patterns."""

    def __init__(self):
        self.agents = {}

    def register(self, agent_id: str, agent: Any, agent_type: AgentType):
        self.agents[agent_id] = {
            "agent": agent,
            "type": agent_type
        }

    async def execute(self, agent_id: str, input_data: Dict):
        entry = self.agents.get(agent_id)
        if not entry:
            raise ValueError(f"Agent {agent_id} not found")

        agent_type = entry["type"]
        agent = entry["agent"]

        if agent_type == AgentType.BASEAGENT:
            return await agent.execute(input_data)
        elif agent_type == AgentType.STANDALONE:
            # Direct method call
            operation = input_data.get("operation")
            return agent.tools[operation](**input_data.get("params", {}))
        elif agent_type == AgentType.CLAUDE_SDK:
            return await agent.query(input_data.get("query"))
```

---

## Best Practices

### 1. Choose the Right Pattern

| Need | Best Pattern |
|------|-------------|
| Production agent | LiMOS BaseAgent |
| Quick prototype | Standalone |
| Claude Code integration | Claude SDK |
| Metrics/monitoring | LiMOS BaseAgent |
| Simple script | Standalone |
| Official tooling | Claude SDK |

### 2. Consistent Error Handling

All patterns should return consistent error formats:

```python
# Success
{"success": True, "result": "...", "metadata": {...}}

# Error
{"success": False, "error": "Error message", "error_code": "ERR_CODE"}
```

### 3. Logging Standards

Use consistent logging across patterns:

```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Agent {self.name} initialized")
logger.error(f"Error in agent: {e}")
```

### 4. Testing All Patterns

Write tests that work with all patterns:

```python
import pytest

@pytest.mark.parametrize("agent_class", [
    BaseAgentImplementation,
    StandaloneImplementation,
    ClaudeSDKImplementation
])
async def test_agent_operation(agent_class):
    agent = agent_class()
    await agent.initialize()
    result = await agent.execute({"operation": "test"})
    assert result["success"] is True
```

---

## Migration Paths

### From Standalone → BaseAgent

```python
# Before (Standalone)
class MyAgent(BaseAgent):
    @tool
    def operation(self):
        return {"result": "..."}

# After (LiMOS BaseAgent)
from core.agents.base import BaseAgent, AgentConfig

class MyAgent(BaseAgent):
    async def _execute(self, input_data, **kwargs):
        operation = input_data.get("operation")
        if operation == "my_operation":
            return {"result": "..."}
```

### From BaseAgent → Claude SDK

```python
# Before (BaseAgent)
async def _execute(self, input_data, **kwargs):
    return {"result": self.process(input_data)}

# After (Claude SDK)
from claude_agent_sdk import tool

@tool("process", "Process data", {"data": str})
async def process_tool(args):
    result = process(args["data"])
    return {"content": [{"type": "text", "text": result}]}
```

---

## Summary

- **LiMOS BaseAgent**: Full-featured, production-ready, metrics, lifecycle
- **Standalone**: Simple, lightweight, easy prototyping
- **Claude SDK**: Official Anthropic, Claude Code integration, MCP

Choose based on your needs, and use integration strategies to combine strengths!
