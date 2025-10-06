# LiMOS - Life Management Operating System

An AI-powered multi-agent system for comprehensive life management, built with Claude Agent SDK 2.0 and FastAPI.

## 🎯 Overview

LiMOS is a sophisticated agent-based application that helps manage various aspects of life through specialized AI agents:

- 💰 **Accounting**: Receipt processing, budgeting, expense tracking
- 🍎 **Nutrition**: Meal planning, calorie tracking, recipe management
- 🛒 **Grocery Management**: Shopping lists, price tracking, inventory
- 🏥 **Health Tracking**: Glucose management, appointments, medications
- 📊 **Productivity**: Tasks, notes, documents, reminders
- 🎣 **Leisure**: Hobby tracking, fishing logs, entertainment

## 🏗️ Architecture

LiMOS uses a hybrid feature-first architecture with:
- **Core Infrastructure**: Base agent system, multi-modal processing
- **Domain Projects**: Independent, scalable domain modules
- **Shared Components**: Reusable utilities and services
- **Agent Coordination**: Hierarchical and event-driven patterns

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js (for Claude Code)
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- Anthropic API Key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/LiMOS.git
cd LiMOS
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp system/config/.env.example system/config/.env
# Edit system/config/.env and add your ANTHROPIC_API_KEY
```

5. Verify setup:
```bash
claude doctor
python -m pytest tests/
```

## 📖 Documentation

- [Architecture Overview](system/docs/architecture/overview.md)
- [Development Setup](system/docs/development/setup.md)
- [Receipt Processing API Guide](projects/accounting/features/receipts/api/README.md)
- [API Client Examples](projects/accounting/features/receipts/api/examples/client_examples.py)

## 🧩 Project Structure

```
LiMOS/
├── core/              # Core infrastructure
├── projects/          # Domain-specific modules
├── shared/            # Cross-project utilities
├── system/            # System configuration
├── storage/           # Data storage
├── tools/             # Development tools
└── tests/             # Test suites
```

## 🛠️ Development

### Running the Receipt Processing API

```bash
# Development mode
cd projects/accounting/features/receipts/api
python main.py

# Or with uvicorn directly
uvicorn projects.accounting.features.receipts.api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoints:**
- **Health Check**: `GET /health` - API status and system health
- **Process Receipt**: `POST /receipts/process` - Upload and process receipt images
- **Get Receipt**: `GET /receipts/{id}` - Retrieve specific receipt
- **Search Receipts**: `POST /receipts/search` - Advanced search with filters
- **Batch Processing**: `POST /batch/process` - Process multiple receipts
- **Export Data**: `POST /receipts/export` - Export receipts to JSON/CSV

**Interactive Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests

```bash
# All tests
pytest

# Specific domain
pytest projects/accounting/tests/

# With coverage
pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy .
```

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Claude Agent SDK](https://docs.anthropic.com/en/docs/claude-code/sdk)
- Powered by [Anthropic's Claude](https://www.anthropic.com/)
- FastAPI framework

## 📧 Contact

Project Link: [https://github.com/YOUR_USERNAME/LiMOS](https://github.com/YOUR_USERNAME/LiMOS)

---

**Status**: 🚧 Under Active Development