# LiMOS Agent Framework

Welcome to the LiMOS Multi-Agent System! This directory contains the core agent framework and documentation for building intelligent agents.

---

## 🚀 Quick Start

### Choose Your Agent Pattern

LiMOS supports **three** production-ready agent patterns:

1. **LiMOS BaseAgent** - Full-featured production framework
2. **Standalone** - Lightweight rapid development
3. **Claude SDK** - Official Anthropic AI integration

Not sure which to use? See [AGENT_COMPARISON.md](./AGENT_COMPARISON.md)

---

## 📚 Documentation

### Essential Reading

| Document | Purpose | Audience |
|----------|---------|----------|
| **[AGENT_COMPARISON.md](./AGENT_COMPARISON.md)** | Compare all three patterns | Everyone |
| **[AGENT_INTEGRATION_GUIDE.md](./AGENT_INTEGRATION_GUIDE.md)** | How to integrate patterns | Developers |
| **[AGENT_SDK_SUMMARY.md](../../AGENT_SDK_SUMMARY.md)** | Project summary & audit results | Project leads |

### Examples

| Example | Pattern | Location |
|---------|---------|----------|
| Receipt Agent | BaseAgent | `projects/accounting/agents/receipt_agent.py` |
| Fleet Manager (BaseAgent) | BaseAgent | `projects/fleet/agents/fleet_manager_agent.py` |
| Fleet Manager (Standalone) | Standalone | `projects/fleet/agents/fleet_manager_agent_compatible.py` |
| Claude SDK Example | Claude SDK | `examples/claude_sdk_agent_example.py` |

---

## 🏗️ Architecture

```
core/agents/
├── base/
│   ├── agent.py              # BaseAgent framework
│   ├── config.py             # Configuration models
│   └── example_agent.py      # BaseAgent example
├── memory/
│   └── memory.py             # Agent memory system
├── registry/
│   └── registry.py           # Agent registry
├── examples/
│   └── claude_sdk_agent_example.py  # Claude SDK example
├── AGENT_COMPARISON.md       # Pattern comparison
├── AGENT_INTEGRATION_GUIDE.md # Integration guide
└── README.md                 # This file
```

---

## 🎯 Pattern Selection Guide

### Use LiMOS BaseAgent When:
- ✅ Building production agents
- ✅ Need metrics and monitoring
- ✅ Require lifecycle management
- ✅ Want status tracking
- ✅ Need timeout handling
- ✅ Integration with LiMOS system

### Use Standalone When:
- ✅ Quick prototyping
- ✅ Simple scripts
- ✅ Learning/teaching
- ✅ No async needed
- ✅ Minimal dependencies

### Use Claude SDK When:
- ✅ Claude Code CLI integration
- ✅ Need conversational AI
- ✅ Want automatic tool routing
- ✅ MCP server development
- ✅ Official Anthropic tooling

---

## 💡 Quick Examples

### Pattern 1: LiMOS BaseAgent

```python
from core.agents.base import BaseAgent, AgentConfig, AgentCapability

class MyAgent(BaseAgent):
    async def _initialize(self):
        # Setup resources
        pass

    async def _execute(self, input_data, **kwargs):
        # Process and return results
        return {"success": True, "result": "..."}

# Usage
config = AgentConfig(
    name="MyAgent",
    capabilities=[AgentCapability.DATA_EXTRACTION]
)
agent = MyAgent(config)
await agent.initialize()
result = await agent.execute({"operation": "process"})
await agent.cleanup()
```

### Pattern 2: Standalone

```python
def tool(func):
    func._is_tool = True
    return func

class MyAgent:
    @tool
    def my_operation(self, param: str):
        return {"success": True, "result": f"Processed {param}"}

# Usage
agent = MyAgent()
result = agent.my_operation("data")
```

### Pattern 3: Claude SDK

```python
from claude_agent_sdk import tool, ClaudeSDKClient, ClaudeAgentOptions

@tool("my_tool", "Description", {"param": str})
async def my_tool(args):
    return {
        "content": [{"type": "text", "text": f"Result: {args['param']}"}]
    }

# Usage
options = ClaudeAgentOptions(system_prompt="You are a helpful assistant")
client = ClaudeSDKClient(options=options)
```

---

## 🧪 Testing

### Test BaseAgent
```bash
cd /Users/ksd/Projects/LiMOS
python3 -c "
import asyncio
from core.agents.base import BaseAgent, AgentConfig

async def test():
    config = AgentConfig(name='Test')
    # Your agent initialization
    print('✅ Test passed')

asyncio.run(test())
"
```

### Test Standalone
```bash
cd /Users/ksd/Projects/LiMOS/projects/fleet
python3 -c "
from agents.fleet_manager_agent_compatible import FleetManagerAgent
agent = FleetManagerAgent(name='Test')
print(f'✅ Agent has {len(agent.tools)} tools')
"
```

### Test Claude SDK
```bash
python3 core/agents/examples/claude_sdk_agent_example.py
```

---

## 📊 Feature Comparison

| Feature | BaseAgent | Standalone | Claude SDK |
|---------|-----------|------------|------------|
| **Async/Await** | ✅ | ❌ | ✅ |
| **Lifecycle** | ✅ | ❌ | ⚠️ |
| **Metrics** | ✅ | ❌ | ❌ |
| **Tool Discovery** | ⚠️ | ✅ | ✅ |
| **Error Handling** | ✅ | ❌ | ⚠️ |
| **Context History** | ✅ | ❌ | ✅ |
| **Status Tracking** | ✅ | ❌ | ❌ |
| **Claude Code** | ❌ | ❌ | ✅ |
| **Learning Curve** | 🔴 High | 🟢 Low | 🟡 Medium |

See [AGENT_COMPARISON.md](./AGENT_COMPARISON.md) for detailed comparison.

---

## 🔧 Common Tasks

### Creating a New Agent

**BaseAgent**:
1. Create class inheriting from `BaseAgent`
2. Implement `_initialize()`, `_execute()`, `_cleanup()`
3. Define `AgentConfig` with capabilities
4. Use async/await throughout

**Standalone**:
1. Create class with `@tool` decorated methods
2. Implement tool discovery (or copy pattern)
3. No async required
4. Direct method invocation

**Claude SDK**:
1. Define tools with `@tool` decorator
2. Create client wrapper class
3. Configure with `ClaudeAgentOptions`
4. Use async/await throughout

### Migrating Between Patterns

See [AGENT_INTEGRATION_GUIDE.md](./AGENT_INTEGRATION_GUIDE.md) for:
- Step-by-step migration guides
- Integration strategies
- Best practices
- Common pitfalls

---

## 📦 Dependencies

### LiMOS BaseAgent
- `anthropic` - For Anthropic API calls
- `pydantic` - Data validation
- Standard library only

### Standalone
- No external dependencies
- Pure Python

### Claude SDK
- `claude-agent-sdk` - Official SDK
- `anthropic` - Anthropic API
- `mcp` - Model Context Protocol

### Installation

```bash
# BaseAgent (already available)
# No additional installation needed

# Claude SDK
pip install claude-agent-sdk

# All dependencies
pip install -r requirements.txt
```

---

## 🎓 Learning Path

### Beginner
1. Read [AGENT_COMPARISON.md](./AGENT_COMPARISON.md)
2. Try Standalone pattern examples
3. Build a simple agent

### Intermediate
1. Read [AGENT_INTEGRATION_GUIDE.md](./AGENT_INTEGRATION_GUIDE.md)
2. Migrate to BaseAgent
3. Add metrics and monitoring

### Advanced
1. Integrate Claude SDK
2. Build multi-agent systems
3. Create custom patterns

---

## 🤝 Contributing

When adding new agents:
1. Choose appropriate pattern
2. Follow existing code style
3. Add comprehensive docstrings
4. Include tests
5. Update documentation

---

## 📞 Support

### Issues & Questions
- Check the comparison guide first
- Review integration guide for examples
- Look at existing agent implementations
- See project summary for audit results

### Resources
- **Comparison Guide**: All three patterns compared
- **Integration Guide**: How to use and integrate
- **Examples**: Working code for all patterns
- **Summary**: Project audit and results

---

## ✅ Status

**Agent Framework**: ✅ Production Ready
**Documentation**: ✅ Complete
**Examples**: ✅ Tested & Working
**Patterns**: ✅ All Three Validated

Last Updated: 2025-10-06
