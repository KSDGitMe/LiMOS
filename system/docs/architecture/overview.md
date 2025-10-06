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
- **API Framework**: FastAPI with async/await patterns
- **Language**: Python 3.10+ with type hints
- **Data Validation**: Pydantic models
- **Authentication**: JWT tokens + API keys
- **Vision Processing**: Claude Vision API for image analysis
- **File Storage**: Local filesystem (cloud storage planned)
- **Database**: In-memory + JSON (PostgreSQL planned)
- **Cache**: In-memory (Redis planned)
- **Testing**: pytest with comprehensive coverage
- **Deployment**: Docker + Docker Compose

## Current Implementation Status

### ✅ Completed Features
- **Base Agent System**: Complete foundation with lifecycle management
- **Receipt Agent**: Specialized agent for receipt processing with Claude Vision
- **FastAPI Integration**: Full REST API with comprehensive endpoints
- **Authentication**: JWT and API key support with rate limiting
- **Batch Processing**: Concurrent processing of multiple receipts
- **File Validation**: Comprehensive upload validation and security
- **Test Coverage**: Extensive test suite for all components

### 🚧 In Development
- Database integration (PostgreSQL)
- Additional domain agents (nutrition, health, etc.)
- Advanced analytics and reporting
- Web frontend interface

### 📋 Planned Features
- Real-time notifications
- Agent coordination workflows
- Cloud storage integration
- Mobile app support