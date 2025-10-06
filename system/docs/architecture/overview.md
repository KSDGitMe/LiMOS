# LiMOS Architecture Overview

## System Design Principles

1. **Feature-First Architecture**: Domain modules are organized by business features
2. **Agent-Based System**: Specialized agents handle specific domains
3. **Multi-Modal Processing**: Support for text, images, audio, PDFs, forms
4. **Unlimited Scalability**: Add new domains without restructuring

## Core Components

### 1. Agent System (core/agents/)
- Base agent classes and interfaces
- Agent coordination patterns
- Memory and context management
- Agent registry and discovery

### 2. Multi-Modal Processing (core/multimodal/)
- Input encoders for different data types
- Fusion strategies for combining modalities
- Storage and caching
- Specialized processors

### 3. Domain Projects (projects/)
Each domain is self-contained with:
- Specialized agents
- Feature modules
- Workflows
- Configuration
- Tests

## Data Flow

```
Input → Encoder → Agent → Processing → Storage → API → User
```

## Technology Stack

- **Agent Framework**: Claude Agent SDK 2.0
- **API**: FastAPI
- **Language**: Python 3.10+
- **Database**: PostgreSQL (planned)
- **Cache**: Redis (planned)
- **Deployment**: Docker + Docker Compose