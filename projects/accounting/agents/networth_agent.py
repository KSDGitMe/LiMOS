"""
Net Worth & Asset Tracking Agent

Tracks net worth, assets, liabilities, and portfolio performance over time.

Key Features:
- Manage assets and liabilities
- Generate net worth snapshots
- Track net worth trends
- Analyze asset allocation
- Monitor portfolio performance
- Set and track net worth goals
- Create debt payoff plans
"""

import sqlite3
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import statistics

from core.agents.base import BaseAgent, AgentConfig
from core.agents.coordination.message_bus import MessageBus, Event
from projects.accounting.models.networth import (
    Asset,
    AssetType,
    Liability,
    LiabilityType,
    ValuationMethod,
    NetWorthSnapshot,
    NetWorthTrend,
    AssetAllocation,
    PortfolioPerformance,
    AssetValuation,
    NetWorthGoal,
    DebtPayoffPlan,
    NetWorthReport,
    MarketData
)


class NetWorthAgent(BaseAgent):
    """
    Net Worth & Asset Tracking Agent

    Responsibilities:
    - Track assets and liabilities
    - Generate net worth snapshots
    - Analyze trends and allocation
    - Monitor portfolio performance
    - Track goals and debt payoff
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.db_path = Path("data/accounting.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.message_bus: Optional[MessageBus] = None

    async def _initialize(self) -> None:
        """Initialize database schema and message bus."""
        await super()._initialize()
        self._setup_database()
        await self._setup_event_subscriptions()

    def _setup_database(self):
        """Create database tables for net worth tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                asset_name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                current_value REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                valuation_method TEXT DEFAULT 'manual',
                last_valuation_date TEXT NOT NULL,
                description TEXT,
                acquisition_date TEXT,
                acquisition_cost REAL,
                ticker_symbol TEXT,
                shares REAL,
                cost_basis REAL,
                location TEXT,
                model TEXT,
                owner TEXT,
                ownership_percentage REAL DEFAULT 100.0,
                linked_account_id TEXT,
                is_active INTEGER DEFAULT 1,
                is_liquid INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags TEXT,
                notes TEXT
            )
        """)

        # Liabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS liabilities (
                liability_id TEXT PRIMARY KEY,
                liability_name TEXT NOT NULL,
                liability_type TEXT NOT NULL,
                current_balance REAL NOT NULL,
                original_amount REAL,
                currency TEXT DEFAULT 'USD',
                interest_rate REAL,
                minimum_payment REAL,
                payment_due_day INTEGER,
                origination_date TEXT,
                maturity_date TEXT,
                last_payment_date TEXT,
                creditor TEXT,
                account_number_last4 TEXT,
                linked_account_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                tags TEXT,
                notes TEXT
            )
        """)

        # Net worth snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networth_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                snapshot_date TEXT NOT NULL,
                total_assets REAL NOT NULL,
                liquid_assets REAL NOT NULL,
                non_liquid_assets REAL NOT NULL,
                assets_by_type TEXT,
                total_liabilities REAL NOT NULL,
                short_term_liabilities REAL NOT NULL,
                long_term_liabilities REAL NOT NULL,
                liabilities_by_type TEXT,
                net_worth REAL NOT NULL,
                liquid_net_worth REAL NOT NULL,
                debt_to_asset_ratio REAL DEFAULT 0.0,
                liquidity_ratio REAL DEFAULT 0.0,
                change_from_previous REAL,
                change_percentage REAL,
                days_since_previous INTEGER,
                asset_details TEXT,
                liability_details TEXT,
                created_at TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Asset valuations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_valuations (
                valuation_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                valuation_date TEXT NOT NULL,
                value REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                valuation_method TEXT NOT NULL,
                previous_value REAL,
                change REAL,
                change_percentage REAL,
                source TEXT,
                verified INTEGER DEFAULT 0,
                verified_by TEXT,
                created_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
            )
        """)

        # Net worth goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS networth_goals (
                goal_id TEXT PRIMARY KEY,
                goal_name TEXT NOT NULL,
                description TEXT,
                target_amount REAL NOT NULL,
                target_date TEXT,
                current_amount REAL NOT NULL,
                amount_remaining REAL NOT NULL,
                percentage_complete REAL NOT NULL,
                is_achieved INTEGER DEFAULT 0,
                achieved_date TEXT,
                milestone_amounts TEXT,
                milestones_reached INTEGER DEFAULT 0,
                projected_completion_date TEXT,
                on_track INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Debt payoff plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debt_payoff_plans (
                plan_id TEXT PRIMARY KEY,
                plan_name TEXT NOT NULL,
                strategy TEXT NOT NULL,
                included_liability_ids TEXT,
                total_debt REAL NOT NULL,
                total_minimum_payment REAL NOT NULL,
                monthly_payment REAL NOT NULL,
                extra_payment REAL DEFAULT 0.0,
                estimated_payoff_date TEXT,
                estimated_months INTEGER,
                total_interest_without_plan REAL DEFAULT 0.0,
                total_interest_with_plan REAL DEFAULT 0.0,
                interest_savings REAL DEFAULT 0.0,
                original_total_debt REAL NOT NULL,
                amount_paid REAL DEFAULT 0.0,
                amount_remaining REAL NOT NULL,
                percentage_complete REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                started_date TEXT,
                completed_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes TEXT
            )
        """)

        # Market data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                market_data_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                price_date TEXT NOT NULL,
                change REAL,
                change_percentage REAL,
                volume INTEGER,
                week_52_high REAL,
                week_52_low REAL,
                source TEXT DEFAULT 'manual',
                fetched_at TEXT NOT NULL
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assets_active ON assets(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_liabilities_type ON liabilities(liability_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_liabilities_active ON liabilities(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_date ON networth_snapshots(snapshot_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_valuations_asset ON asset_valuations(asset_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol)")

        conn.commit()
        conn.close()

    async def _setup_event_subscriptions(self):
        """Subscribe to relevant events."""
        from core.agents.coordination.message_bus import get_default_message_bus
        self.message_bus = get_default_message_bus()

    async def _execute(self, task: Dict) -> Dict:
        """Execute net worth operations."""
        operation = task.get("operation")
        parameters = task.get("parameters", {})

        operations = {
            # Asset operations
            "create_asset": self.create_asset,
            "update_asset": self.update_asset,
            "get_asset": self.get_asset,
            "list_assets": self.list_assets,
            "delete_asset": self.delete_asset,
            "record_valuation": self.record_valuation,

            # Liability operations
            "create_liability": self.create_liability,
            "update_liability": self.update_liability,
            "get_liability": self.get_liability,
            "list_liabilities": self.list_liabilities,
            "delete_liability": self.delete_liability,

            # Net worth operations
            "create_snapshot": self.create_snapshot,
            "get_snapshot": self.get_snapshot,
            "list_snapshots": self.list_snapshots,
            "analyze_trends": self.analyze_trends,

            # Analysis
            "analyze_allocation": self.analyze_allocation,
            "calculate_portfolio_performance": self.calculate_portfolio_performance,

            # Goals
            "create_goal": self.create_goal,
            "update_goal_progress": self.update_goal_progress,
            "get_goal": self.get_goal,
            "list_goals": self.list_goals,

            # Debt management
            "create_payoff_plan": self.create_payoff_plan,
            "update_payoff_plan": self.update_payoff_plan,
            "get_payoff_plan": self.get_payoff_plan,

            # Reports
            "generate_networth_report": self.generate_networth_report
        }

        if operation not in operations:
            return {
                "status": "error",
                "error": f"Unknown operation: {operation}",
                "available_operations": list(operations.keys())
            }

        try:
            result = await operations[operation](**parameters)
            return {"status": "success", "result": result}
        except Exception as e:
            self.logger.error(f"Error executing {operation}: {e}")
            return {"status": "error", "error": str(e)}

    async def create_asset(self, asset_data: Dict) -> Dict:
        """Create a new asset."""
        import json

        asset = Asset(**asset_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO assets (
                asset_id, asset_name, asset_type, current_value, currency,
                valuation_method, last_valuation_date, description,
                acquisition_date, acquisition_cost, ticker_symbol, shares,
                cost_basis, location, model, owner, ownership_percentage,
                linked_account_id, is_active, is_liquid, created_at,
                updated_at, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset.asset_id,
            asset.asset_name,
            asset.asset_type.value,
            asset.current_value,
            asset.currency,
            asset.valuation_method.value,
            asset.last_valuation_date.isoformat(),
            asset.description,
            asset.acquisition_date.isoformat() if asset.acquisition_date else None,
            asset.acquisition_cost,
            asset.ticker_symbol,
            asset.shares,
            asset.cost_basis,
            asset.location,
            asset.model,
            asset.owner,
            asset.ownership_percentage,
            asset.linked_account_id,
            1 if asset.is_active else 0,
            1 if asset.is_liquid else 0,
            asset.created_at.isoformat(),
            asset.updated_at.isoformat(),
            json.dumps(asset.tags),
            asset.notes
        ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="asset.created",
                payload={"asset": asset.dict()},
                source_agent=self.agent_id
            )

        return asset.dict()

    async def update_asset(self, asset_id: str, updates: Dict) -> Dict:
        """Update asset value or details."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build update query
        update_fields = []
        params = []

        if "current_value" in updates:
            update_fields.append("current_value = ?")
            params.append(updates["current_value"])
            update_fields.append("last_valuation_date = ?")
            params.append(date.today().isoformat())

        update_fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(asset_id)

        query = f"UPDATE assets SET {', '.join(update_fields)} WHERE asset_id = ?"
        cursor.execute(query, params)

        conn.commit()
        conn.close()

        return {"asset_id": asset_id, "updated": True}

    async def get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get asset by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "asset_id": row[0],
            "asset_name": row[1],
            "asset_type": row[2],
            "current_value": row[3],
            "is_active": bool(row[18])
        }

    async def list_assets(
        self,
        asset_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict]:
        """List assets with filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM assets WHERE is_active = ?"
        params = [1 if is_active else 0]

        if asset_type:
            query += " AND asset_type = ?"
            params.append(asset_type)

        cursor.execute(query, params)

        assets = []
        for row in cursor.fetchall():
            assets.append({
                "asset_id": row[0],
                "asset_name": row[1],
                "asset_type": row[2],
                "current_value": row[3]
            })

        conn.close()
        return assets

    async def delete_asset(self, asset_id: str) -> Dict:
        """Soft delete asset."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE assets
            SET is_active = 0, updated_at = ?
            WHERE asset_id = ?
        """, (datetime.utcnow().isoformat(), asset_id))

        conn.commit()
        conn.close()

        return {"asset_id": asset_id, "deleted": True}

    async def record_valuation(self, valuation_data: Dict) -> Dict:
        """Record asset valuation."""
        valuation = AssetValuation(**valuation_data)

        # Get previous value
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT value FROM asset_valuations
            WHERE asset_id = ?
            ORDER BY valuation_date DESC
            LIMIT 1
        """, (valuation.asset_id,))

        row = cursor.fetchone()
        if row:
            valuation.previous_value = row[0]
            valuation.change = valuation.value - valuation.previous_value
            if valuation.previous_value > 0:
                valuation.change_percentage = (valuation.change / valuation.previous_value) * 100

        # Save valuation
        cursor.execute("""
            INSERT INTO asset_valuations (
                valuation_id, asset_id, valuation_date, value, currency,
                valuation_method, previous_value, change, change_percentage,
                source, verified, verified_by, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            valuation.valuation_id,
            valuation.asset_id,
            valuation.valuation_date.isoformat(),
            valuation.value,
            valuation.currency,
            valuation.valuation_method.value,
            valuation.previous_value,
            valuation.change,
            valuation.change_percentage,
            valuation.source,
            1 if valuation.verified else 0,
            valuation.verified_by,
            valuation.created_at.isoformat(),
            valuation.notes
        ))

        # Update asset
        cursor.execute("""
            UPDATE assets
            SET current_value = ?,
                last_valuation_date = ?,
                updated_at = ?
            WHERE asset_id = ?
        """, (
            valuation.value,
            valuation.valuation_date.isoformat(),
            datetime.utcnow().isoformat(),
            valuation.asset_id
        ))

        conn.commit()
        conn.close()

        return valuation.dict()

    async def create_liability(self, liability_data: Dict) -> Dict:
        """Create a new liability."""
        import json

        liability = Liability(**liability_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO liabilities (
                liability_id, liability_name, liability_type, current_balance,
                original_amount, currency, interest_rate, minimum_payment,
                payment_due_day, origination_date, maturity_date,
                last_payment_date, creditor, account_number_last4,
                linked_account_id, is_active, created_at, updated_at, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            liability.liability_id,
            liability.liability_name,
            liability.liability_type.value,
            liability.current_balance,
            liability.original_amount,
            liability.currency,
            liability.interest_rate,
            liability.minimum_payment,
            liability.payment_due_day,
            liability.origination_date.isoformat() if liability.origination_date else None,
            liability.maturity_date.isoformat() if liability.maturity_date else None,
            liability.last_payment_date.isoformat() if liability.last_payment_date else None,
            liability.creditor,
            liability.account_number_last4,
            liability.linked_account_id,
            1 if liability.is_active else 0,
            liability.created_at.isoformat(),
            liability.updated_at.isoformat(),
            json.dumps(liability.tags),
            liability.notes
        ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="liability.created",
                payload={"liability": liability.dict()},
                source_agent=self.agent_id
            )

        return liability.dict()

    async def update_liability(self, liability_id: str, updates: Dict) -> Dict:
        """Update liability balance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        update_fields = []
        params = []

        if "current_balance" in updates:
            update_fields.append("current_balance = ?")
            params.append(updates["current_balance"])

        update_fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(liability_id)

        query = f"UPDATE liabilities SET {', '.join(update_fields)} WHERE liability_id = ?"
        cursor.execute(query, params)

        conn.commit()
        conn.close()

        return {"liability_id": liability_id, "updated": True}

    async def get_liability(self, liability_id: str) -> Optional[Dict]:
        """Get liability by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM liabilities WHERE liability_id = ?", (liability_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "liability_id": row[0],
            "liability_name": row[1],
            "liability_type": row[2],
            "current_balance": row[3]
        }

    async def list_liabilities(
        self,
        liability_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict]:
        """List liabilities with filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM liabilities WHERE is_active = ?"
        params = [1 if is_active else 0]

        if liability_type:
            query += " AND liability_type = ?"
            params.append(liability_type)

        cursor.execute(query, params)

        liabilities = []
        for row in cursor.fetchall():
            liabilities.append({
                "liability_id": row[0],
                "liability_name": row[1],
                "liability_type": row[2],
                "current_balance": row[3]
            })

        conn.close()
        return liabilities

    async def delete_liability(self, liability_id: str) -> Dict:
        """Soft delete liability."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE liabilities
            SET is_active = 0, updated_at = ?
            WHERE liability_id = ?
        """, (datetime.utcnow().isoformat(), liability_id))

        conn.commit()
        conn.close()

        return {"liability_id": liability_id, "deleted": True}

    async def create_snapshot(self, snapshot_date: Optional[str] = None) -> Dict:
        """Create net worth snapshot."""
        import json

        snap_date = date.fromisoformat(snapshot_date) if snapshot_date else date.today()

        # Get all active assets
        assets = await self.list_assets(is_active=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate asset totals
        total_assets = 0.0
        liquid_assets = 0.0
        non_liquid_assets = 0.0
        assets_by_type = {}

        for asset_summary in assets:
            cursor.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_summary["asset_id"],))
            asset_row = cursor.fetchone()

            if asset_row:
                value = asset_row[3]
                asset_type = asset_row[2]
                is_liquid = bool(asset_row[19])

                total_assets += value
                if is_liquid:
                    liquid_assets += value
                else:
                    non_liquid_assets += value

                assets_by_type[asset_type] = assets_by_type.get(asset_type, 0) + value

        # Get all active liabilities
        liabilities = await self.list_liabilities(is_active=True)
        total_liabilities = 0.0
        liabilities_by_type = {}

        for liab_summary in liabilities:
            cursor.execute("SELECT * FROM liabilities WHERE liability_id = ?", (liab_summary["liability_id"],))
            liab_row = cursor.fetchone()

            if liab_row:
                balance = liab_row[3]
                liab_type = liab_row[2]

                total_liabilities += balance
                liabilities_by_type[liab_type] = liabilities_by_type.get(liab_type, 0) + balance

        # Calculate net worth
        net_worth = total_assets - total_liabilities
        liquid_net_worth = liquid_assets - total_liabilities

        # Calculate ratios
        debt_to_asset_ratio = (total_liabilities / total_assets) if total_assets > 0 else 0
        liquidity_ratio = (liquid_assets / total_liabilities) if total_liabilities > 0 else 0

        # Get previous snapshot for change calculation
        cursor.execute("""
            SELECT snapshot_date, net_worth FROM networth_snapshots
            ORDER BY snapshot_date DESC
            LIMIT 1
        """)
        prev_row = cursor.fetchone()

        change_from_previous = None
        change_percentage = None
        days_since_previous = None

        if prev_row:
            prev_date = date.fromisoformat(prev_row[0])
            prev_net_worth = prev_row[1]
            change_from_previous = net_worth - prev_net_worth
            if prev_net_worth != 0:
                change_percentage = (change_from_previous / prev_net_worth) * 100
            days_since_previous = (snap_date - prev_date).days

        # Create snapshot
        snapshot = NetWorthSnapshot(
            snapshot_date=snap_date,
            total_assets=total_assets,
            liquid_assets=liquid_assets,
            non_liquid_assets=non_liquid_assets,
            assets_by_type=assets_by_type,
            total_liabilities=total_liabilities,
            short_term_liabilities=total_liabilities,  # Simplified
            long_term_liabilities=0.0,
            liabilities_by_type=liabilities_by_type,
            net_worth=net_worth,
            liquid_net_worth=liquid_net_worth,
            debt_to_asset_ratio=debt_to_asset_ratio,
            liquidity_ratio=liquidity_ratio,
            change_from_previous=change_from_previous,
            change_percentage=change_percentage,
            days_since_previous=days_since_previous
        )

        # Save snapshot
        cursor.execute("""
            INSERT INTO networth_snapshots (
                snapshot_id, snapshot_date, total_assets, liquid_assets,
                non_liquid_assets, assets_by_type, total_liabilities,
                short_term_liabilities, long_term_liabilities, liabilities_by_type,
                net_worth, liquid_net_worth, debt_to_asset_ratio, liquidity_ratio,
                change_from_previous, change_percentage, days_since_previous,
                asset_details, liability_details, created_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot.snapshot_id,
            snapshot.snapshot_date.isoformat(),
            snapshot.total_assets,
            snapshot.liquid_assets,
            snapshot.non_liquid_assets,
            json.dumps(snapshot.assets_by_type),
            snapshot.total_liabilities,
            snapshot.short_term_liabilities,
            snapshot.long_term_liabilities,
            json.dumps(snapshot.liabilities_by_type),
            snapshot.net_worth,
            snapshot.liquid_net_worth,
            snapshot.debt_to_asset_ratio,
            snapshot.liquidity_ratio,
            snapshot.change_from_previous,
            snapshot.change_percentage,
            snapshot.days_since_previous,
            json.dumps(snapshot.asset_details),
            json.dumps(snapshot.liability_details),
            snapshot.created_at.isoformat(),
            snapshot.notes
        ))

        conn.commit()
        conn.close()

        # Publish event
        if self.message_bus:
            await self.message_bus.publish(
                event_type="networth.snapshot_created",
                payload={"snapshot": snapshot.dict()},
                source_agent=self.agent_id
            )

        return snapshot.dict()

    async def get_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """Get snapshot by ID."""
        import json

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM networth_snapshots WHERE snapshot_id = ?", (snapshot_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "snapshot_id": row[0],
            "snapshot_date": row[1],
            "net_worth": row[10],
            "total_assets": row[2],
            "total_liabilities": row[6]
        }

    async def list_snapshots(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """List net worth snapshots."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM networth_snapshots WHERE 1=1"
        params = []

        if start_date:
            query += " AND snapshot_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND snapshot_date <= ?"
            params.append(end_date)

        query += " ORDER BY snapshot_date DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        snapshots = []
        for row in cursor.fetchall():
            snapshots.append({
                "snapshot_id": row[0],
                "snapshot_date": row[1],
                "net_worth": row[10],
                "total_assets": row[2],
                "total_liabilities": row[6],
                "change_percentage": row[15]
            })

        conn.close()
        return snapshots

    async def analyze_trends(
        self,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Analyze net worth trends."""
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        # Get snapshots
        snapshots_data = await self.list_snapshots(start_date, end_date, limit=1000)

        if not snapshots_data:
            return {"error": "No snapshots found"}

        net_worth_values = [s["net_worth"] for s in snapshots_data]

        # Calculate statistics
        starting_nw = snapshots_data[-1]["net_worth"]
        ending_nw = snapshots_data[0]["net_worth"]
        total_change = ending_nw - starting_nw
        total_change_pct = (total_change / starting_nw * 100) if starting_nw != 0 else 0

        avg_nw = statistics.mean(net_worth_values)
        median_nw = statistics.median(net_worth_values)
        min_nw = min(net_worth_values)
        max_nw = max(net_worth_values)

        # Calculate growth rates
        days = (end - start).days
        months = days / 30.0
        avg_monthly_growth = (total_change / months) if months > 0 else 0

        # Create trend analysis
        trend = NetWorthTrend(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            snapshot_count=len(snapshots_data),
            starting_net_worth=starting_nw,
            ending_net_worth=ending_nw,
            total_change=total_change,
            total_change_percentage=total_change_pct,
            average_net_worth=avg_nw,
            median_net_worth=median_nw,
            min_net_worth=min_nw,
            max_net_worth=max_nw,
            average_monthly_growth=avg_monthly_growth,
            annualized_growth_rate=0.0  # Simplified
        )

        return trend.dict()

    async def analyze_allocation(self) -> Dict:
        """Analyze current asset allocation."""
        import json

        # Get current assets
        assets = await self.list_assets(is_active=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        total_value = 0.0
        allocation_by_type = {}
        liquid_assets = 0.0
        non_liquid_assets = 0.0

        for asset_summary in assets:
            cursor.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_summary["asset_id"],))
            row = cursor.fetchone()

            if row:
                value = row[3]
                asset_type = row[2]
                is_liquid = bool(row[19])

                total_value += value
                allocation_by_type[asset_type] = allocation_by_type.get(asset_type, 0) + value

                if is_liquid:
                    liquid_assets += value
                else:
                    non_liquid_assets += value

        conn.close()

        # Calculate percentages
        allocation_pct = {
            k: (v / total_value * 100) if total_value > 0 else 0
            for k, v in allocation_by_type.items()
        }

        liquid_pct = (liquid_assets / total_value * 100) if total_value > 0 else 0
        non_liquid_pct = (non_liquid_assets / total_value * 100) if total_value > 0 else 0

        # Create allocation analysis
        allocation = AssetAllocation(
            as_of_date=date.today(),
            total_value=total_value,
            allocation_by_type=allocation_by_type,
            allocation_percentage_by_type=allocation_pct,
            liquid_assets=liquid_assets,
            liquid_percentage=liquid_pct,
            non_liquid_assets=non_liquid_assets,
            non_liquid_percentage=non_liquid_pct
        )

        return allocation.dict()

    async def calculate_portfolio_performance(
        self,
        start_date: str,
        end_date: str
    ) -> Dict:
        """Calculate investment portfolio performance."""
        # Simplified implementation
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        performance = PortfolioPerformance(
            start_date=start,
            end_date=end,
            period_label=f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            starting_value=0.0,
            ending_value=0.0,
            total_return=0.0,
            total_return_percentage=0.0
        )

        return performance.dict()

    async def create_goal(self, goal_data: Dict) -> Dict:
        """Create net worth goal."""
        import json

        goal = NetWorthGoal(**goal_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO networth_goals (
                goal_id, goal_name, description, target_amount, target_date,
                current_amount, amount_remaining, percentage_complete,
                is_achieved, achieved_date, milestone_amounts, milestones_reached,
                projected_completion_date, on_track, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            goal.goal_id,
            goal.goal_name,
            goal.description,
            goal.target_amount,
            goal.target_date.isoformat() if goal.target_date else None,
            goal.current_amount,
            goal.amount_remaining,
            goal.percentage_complete,
            1 if goal.is_achieved else 0,
            goal.achieved_date.isoformat() if goal.achieved_date else None,
            json.dumps(goal.milestone_amounts),
            goal.milestones_reached,
            goal.projected_completion_date.isoformat() if goal.projected_completion_date else None,
            1 if goal.on_track else 0,
            goal.created_at.isoformat(),
            goal.updated_at.isoformat()
        ))

        conn.commit()
        conn.close()

        return goal.dict()

    async def update_goal_progress(self, goal_id: str, current_amount: float) -> Dict:
        """Update goal progress."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get goal
        cursor.execute("SELECT target_amount FROM networth_goals WHERE goal_id = ?", (goal_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"error": "Goal not found"}

        target = row[0]
        remaining = target - current_amount
        pct_complete = (current_amount / target * 100) if target > 0 else 0
        is_achieved = current_amount >= target

        # Update goal
        cursor.execute("""
            UPDATE networth_goals
            SET current_amount = ?,
                amount_remaining = ?,
                percentage_complete = ?,
                is_achieved = ?,
                updated_at = ?
            WHERE goal_id = ?
        """, (
            current_amount,
            remaining,
            pct_complete,
            1 if is_achieved else 0,
            datetime.utcnow().isoformat(),
            goal_id
        ))

        conn.commit()
        conn.close()

        return {
            "goal_id": goal_id,
            "current_amount": current_amount,
            "percentage_complete": pct_complete,
            "is_achieved": is_achieved
        }

    async def get_goal(self, goal_id: str) -> Optional[Dict]:
        """Get goal by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM networth_goals WHERE goal_id = ?", (goal_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "goal_id": row[0],
            "goal_name": row[1],
            "target_amount": row[3],
            "current_amount": row[5],
            "percentage_complete": row[7],
            "is_achieved": bool(row[8])
        }

    async def list_goals(self, is_achieved: Optional[bool] = None) -> List[Dict]:
        """List net worth goals."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM networth_goals WHERE 1=1"
        params = []

        if is_achieved is not None:
            query += " AND is_achieved = ?"
            params.append(1 if is_achieved else 0)

        cursor.execute(query, params)

        goals = []
        for row in cursor.fetchall():
            goals.append({
                "goal_id": row[0],
                "goal_name": row[1],
                "target_amount": row[3],
                "current_amount": row[5],
                "percentage_complete": row[7]
            })

        conn.close()
        return goals

    async def create_payoff_plan(self, plan_data: Dict) -> Dict:
        """Create debt payoff plan."""
        import json

        plan = DebtPayoffPlan(**plan_data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO debt_payoff_plans (
                plan_id, plan_name, strategy, included_liability_ids, total_debt,
                total_minimum_payment, monthly_payment, extra_payment,
                estimated_payoff_date, estimated_months, total_interest_without_plan,
                total_interest_with_plan, interest_savings, original_total_debt,
                amount_paid, amount_remaining, percentage_complete, is_active,
                started_date, completed_date, created_at, updated_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan.plan_id,
            plan.plan_name,
            plan.strategy,
            json.dumps(plan.included_liability_ids),
            plan.total_debt,
            plan.total_minimum_payment,
            plan.monthly_payment,
            plan.extra_payment,
            plan.estimated_payoff_date.isoformat() if plan.estimated_payoff_date else None,
            plan.estimated_months,
            plan.total_interest_without_plan,
            plan.total_interest_with_plan,
            plan.interest_savings,
            plan.original_total_debt,
            plan.amount_paid,
            plan.amount_remaining,
            plan.percentage_complete,
            1 if plan.is_active else 0,
            plan.started_date.isoformat() if plan.started_date else None,
            plan.completed_date.isoformat() if plan.completed_date else None,
            plan.created_at.isoformat(),
            plan.updated_at.isoformat(),
            plan.notes
        ))

        conn.commit()
        conn.close()

        return plan.dict()

    async def update_payoff_plan(self, plan_id: str, amount_paid: float) -> Dict:
        """Update debt payoff plan progress."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get plan
        cursor.execute("SELECT original_total_debt FROM debt_payoff_plans WHERE plan_id = ?", (plan_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {"error": "Plan not found"}

        original_debt = row[0]
        remaining = original_debt - amount_paid
        pct_complete = (amount_paid / original_debt * 100) if original_debt > 0 else 0

        # Update plan
        cursor.execute("""
            UPDATE debt_payoff_plans
            SET amount_paid = ?,
                amount_remaining = ?,
                percentage_complete = ?,
                updated_at = ?
            WHERE plan_id = ?
        """, (
            amount_paid,
            remaining,
            pct_complete,
            datetime.utcnow().isoformat(),
            plan_id
        ))

        conn.commit()
        conn.close()

        return {
            "plan_id": plan_id,
            "amount_paid": amount_paid,
            "percentage_complete": pct_complete
        }

    async def get_payoff_plan(self, plan_id: str) -> Optional[Dict]:
        """Get payoff plan by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM debt_payoff_plans WHERE plan_id = ?", (plan_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "plan_id": row[0],
            "plan_name": row[1],
            "strategy": row[2],
            "total_debt": row[4],
            "monthly_payment": row[6],
            "percentage_complete": row[16]
        }

    async def generate_networth_report(self) -> Dict:
        """Generate comprehensive net worth report."""
        # Create current snapshot
        snapshot_data = await self.create_snapshot()
        snapshot = NetWorthSnapshot(**snapshot_data)

        # Get allocation
        allocation_data = await self.analyze_allocation()
        allocation = AssetAllocation(**allocation_data)

        # Get goals
        goals_data = await self.list_goals(is_achieved=False)

        # Create report
        report = NetWorthReport(
            report_date=date.today(),
            current_snapshot=snapshot,
            asset_allocation=allocation,
            goals_progress=[]  # Simplified
        )

        return report.dict()
