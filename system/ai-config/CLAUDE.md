# LiMOS Claude Configuration

This is the root Claude configuration for the entire LiMOS project.

## Project Context

LiMOS (Life Management Operating System) is a multi-agent AI application built with Claude Agent SDK 2.0.

## Working Directory

Root: `/LiMOS/`

## Architecture Pattern

- Feature-first organization
- Agent-based system design
- Domain-driven development
- Multi-modal input processing

## Key Directories

- `core/`: Core infrastructure and base classes
- `projects/`: Domain-specific agent implementations
- `shared/`: Cross-project utilities
- `system/`: System configuration and documentation

## Development Guidelines

1. Each domain (accounting, nutrition, etc.) is independent
2. Agents inherit from BaseAgent in core/agents/base/
3. Follow the feature/function organization pattern
4. Use async/await throughout
5. Implement comprehensive tests
6. Document all public APIs

## Code Standards

- Python: Black formatting, type hints
- API: FastAPI best practices
- Testing: pytest with async support
- Docs: Markdown with examples

## Agent Development

When creating new agents:
1. Inherit from BaseAgent
2. Define clear system prompts
3. Implement custom tools if needed
4. Add to agent registry
5. Create comprehensive tests