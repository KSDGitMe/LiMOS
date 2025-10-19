#!/usr/bin/env python3
"""
LiMOS Unified API Server Launcher

Starts the unified API server serving all LiMOS modules on port 8000.
"""

import uvicorn
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Load environment variables from .env file
env_path = Path(project_root) / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")


def main():
    """Launch the unified API server."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║            LiMOS Unified API Server                      ║
    ╠══════════════════════════════════════════════════════════╣
    ║  URL: http://localhost:9000                              ║
    ║  Docs: http://localhost:9000/docs                        ║
    ║  Modules:                                                 ║
    ║    - Accounting: /api/accounting/*                       ║
    ║    - Fleet:      /api/fleet/*                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "projects.api.main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
