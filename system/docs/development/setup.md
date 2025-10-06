# Development Setup Guide

## Prerequisites

1. Python 3.10 or higher
2. Node.js 18+ and npm
3. Git
4. Docker (optional, for containerized development)
5. Anthropic API key

## Initial Setup

### 1. Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
claude doctor
```

### 2. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/LiMOS.git
cd LiMOS
```

### 3. Python Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configuration
```bash
cp system/config/.env.example system/config/.env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 5. Verify Setup
```bash
pytest tests/ -v
```

## Development Workflow

1. Create feature branch
2. Implement changes
3. Run tests
4. Submit PR

## Running Locally

```bash
uvicorn projects.accounting.features.receipts.api.main:app --reload
```

## Testing

```bash
pytest
pytest --cov
```