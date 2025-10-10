#!/usr/bin/env python3
"""
Run the LiMOS Accounting API Server

This script properly sets up the Python path and starts the FastAPI server.
"""

import sys
import os
from pathlib import Path

# Add the LiMOS root directory to Python path
limos_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(limos_root))

# Now we can run uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "projects.accounting.api.main:app",  # Use in-memory API for development
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
