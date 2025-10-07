"""
FastAPI Application for Accounting Module

Main FastAPI application that coordinates all accounting agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict, Any

from core.agents.base import AgentConfig
from projects.accounting.agents import (
    TransactionManagementAgent,
    CashFlowForecastingAgent,
    BudgetManagementAgent,
    ReconciliationAgent,
    ReportingAgent,
    NetWorthAgent
)

# Agent instances (initialized on startup)
agents: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agents on startup, cleanup on shutdown."""
    # Startup: Initialize all agents
    agents["transaction"] = TransactionManagementAgent(
        AgentConfig(name="TransactionManagementAgent")
    )
    agents["forecasting"] = CashFlowForecastingAgent(
        AgentConfig(name="CashFlowForecastingAgent")
    )
    agents["budget"] = BudgetManagementAgent(
        AgentConfig(name="BudgetManagementAgent")
    )
    agents["reconciliation"] = ReconciliationAgent(
        AgentConfig(name="ReconciliationAgent")
    )
    agents["reporting"] = ReportingAgent(
        AgentConfig(name="ReportingAgent")
    )
    agents["networth"] = NetWorthAgent(
        AgentConfig(name="NetWorthAgent")
    )

    # Initialize all agents
    for agent in agents.values():
        await agent.initialize()

    yield

    # Shutdown: Cleanup
    for agent in agents.values():
        await agent.shutdown()


# Create FastAPI app
app = FastAPI(
    title="Accounting Module API",
    description="REST API for personal finance management with 6 specialized agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import routers
from .routers import (
    transactions,
    forecasting,
    budgets,
    reconciliation,
    reporting,
    networth
)

# Include routers
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(forecasting.router, prefix="/api/v1/forecasting", tags=["Forecasting"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Budgets"])
app.include_router(reconciliation.router, prefix="/api/v1/reconciliation", tags=["Reconciliation"])
app.include_router(reporting.router, prefix="/api/v1/reporting", tags=["Reporting"])
app.include_router(networth.router, prefix="/api/v1/networth", tags=["Net Worth"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Accounting Module API",
        "version": "1.0.0",
        "agents": {
            "transaction_management": "Manage transactions and recurring schedules",
            "cash_flow_forecasting": "Project account balances with confidence intervals",
            "budget_management": "Track budgets with real-time alerts",
            "reconciliation": "Match statements and process payments",
            "reporting_analytics": "Generate reports, insights, and KPIs",
            "networth_tracking": "Track assets, liabilities, and net worth goals"
        },
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents_initialized": len(agents),
        "agents": list(agents.keys())
    }


def get_agent(agent_name: str):
    """Get agent instance by name."""
    if agent_name not in agents:
        raise HTTPException(status_code=500, detail=f"Agent {agent_name} not initialized")
    return agents[agent_name]
