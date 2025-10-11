#!/usr/bin/env python3
"""
Run the Fleet Management API Server

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
        "projects.fleet.api.main:app",
        host="0.0.0.0",
        port=8001,  # Different port from accounting API
        reload=True,
        log_level="info"
    )
