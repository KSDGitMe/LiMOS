#!/usr/bin/env python3
"""
Simplified Receipt Processing FastAPI Application

A basic version that can run without the full agent system for testing.
"""

import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="LiMOS Receipt Processing API",
    description="AI-powered receipt processing and management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LiMOS Receipt Processing API",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-powered receipt processing and management system",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "receipts": "/receipts"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "message": "API is running successfully"
    }

@app.get("/receipts")
async def list_receipts():
    """List receipts endpoint (demo)."""
    return {
        "receipts": [
            {
                "receipt_id": "demo-001",
                "vendor_name": "Demo Store",
                "total_amount": 25.99,
                "date": "2024-01-15T10:30:00Z",
                "status": "processed"
            },
            {
                "receipt_id": "demo-002",
                "vendor_name": "Another Store",
                "total_amount": 15.49,
                "date": "2024-01-14T14:20:00Z",
                "status": "processed"
            }
        ],
        "total_count": 2,
        "message": "This is demo data. Full functionality requires the complete agent system."
    }

if __name__ == "__main__":
    print("🚀 Starting LiMOS Receipt Processing API (Simplified)...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )