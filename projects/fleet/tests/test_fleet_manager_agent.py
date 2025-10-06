#!/usr/bin/env python3
"""
Test Suite for Fleet Manager Agent

Comprehensive tests demonstrating all agent capabilities including:
- Vehicle management
- Fuel event logging with multi-modal inputs
- Maintenance and repair tracking
- Cost calculations
- Accounting notifications
- Database persistence
"""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add the parent directory to the path to import the agent
import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.fleet_manager_agent_compatible import FleetManagerAgent, FleetDatabase


class TestFleetManagerAgent(unittest.TestCase):
    """Test suite for Fleet Manager Agent functionality."""

    def setUp(self):
        """Set up test environment with temporary database."""
        # Create temporary database file
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.test_db_fd)

        # Initialize agent with test database
        self.agent = FleetManagerAgent(name="TestFleetAgent")
        self.agent.database = FleetDatabase(self.test_db_path)

    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary database file
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)

    def test_add_vehicle(self):
        """Test adding a vehicle to the fleet."""
        result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001",
            color="Red",
            engine_type="4-Cylinder"
        )

        self.assertTrue(result["success"])
        self.assertIn("vehicle_id", result)
        self.assertIn("Honda Civic", result["message"])

        # Verify vehicle is in agent's memory
        vehicle_id = result["vehicle_id"]
        self.assertIn(vehicle_id, self.agent.vehicles)

        # Verify vehicle is in database
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "1HGCM82633A123456")  # VIN
            self.assertEqual(row[2], "Honda")  # Make
            self.assertEqual(row[3], "Civic")  # Model

    def test_log_fuel_event_with_price_per_gallon(self):
        """Test logging fuel event with price per gallon (calculates total cost)."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log fuel event with price per gallon
        result = self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=15.2,
            odometer_reading=50000,
            fuel_type="Gasoline",
            price_per_gallon=3.45,
            station_name="Exxon",
            latitude=41.8781,
            longitude=-87.6298
        )

        self.assertTrue(result["success"])
        self.assertIn("fuel_id", result)

        # Check calculations
        calculations = result["calculations"]
        expected_total = 15.2 * 3.45
        self.assertAlmostEqual(calculations["total_cost"], expected_total, places=2)
        self.assertAlmostEqual(calculations["price_per_gallon"], 3.45, places=2)

        # Check accounting notification
        self.assertTrue(result["accounting_notification"]["success"])

    def test_log_fuel_event_with_total_cost(self):
        """Test logging fuel event with total cost (calculates price per gallon)."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log fuel event with total cost
        result = self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=12.0,
            odometer_reading=50200,
            fuel_type="Gasoline",
            total_cost=38.50,
            station_name="Shell",
            receipt_image_path="/path/to/receipt.jpg"
        )

        self.assertTrue(result["success"])

        # Check calculations
        calculations = result["calculations"]
        expected_price_per_gallon = 38.50 / 12.0
        self.assertAlmostEqual(calculations["price_per_gallon"], expected_price_per_gallon, places=2)
        self.assertAlmostEqual(calculations["total_cost"], 38.50, places=2)

    def test_log_maintenance_event(self):
        """Test logging maintenance event."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log maintenance event
        result = self.agent.log_maintenance_event(
            vehicle_id=vehicle_id,
            maintenance_type="Oil Change",
            description="Regular oil change and filter replacement",
            cost=45.99,
            vendor="Quick Lube",
            odometer_reading=50000,
            next_service_due=53000,
            parts_replaced=["Oil Filter", "Engine Oil", "Air Filter"]
        )

        self.assertTrue(result["success"])
        self.assertIn("maintenance_id", result)

        # Check calculations
        calculations = result["calculations"]
        self.assertIsNotNone(calculations["cost_per_mile"])
        self.assertEqual(calculations["total_maintenance_costs"], 45.99)

        # Check accounting notification
        self.assertTrue(result["accounting_notification"]["success"])

    def test_log_repair_event(self):
        """Test logging repair event."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log repair event
        result = self.agent.log_repair_event(
            vehicle_id=vehicle_id,
            repair_type="Brake Repair",
            description="Replaced front brake pads and rotors",
            cost=285.50,
            vendor="AutoCare Center",
            odometer_reading=52000,
            warranty_info="12 months or 12,000 miles",
            severity="High"
        )

        self.assertTrue(result["success"])
        self.assertIn("repair_id", result)

        # Check calculations
        calculations = result["calculations"]
        self.assertEqual(calculations["total_repair_costs"], 285.50)
        self.assertEqual(calculations["severity"], "High")

        # Check accounting notification
        self.assertTrue(result["accounting_notification"]["success"])

    def test_fuel_efficiency_calculation(self):
        """Test fuel efficiency calculation with multiple fuel events."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log multiple fuel events
        self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=12.0,
            odometer_reading=45000,
            price_per_gallon=3.25
        )

        self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=11.5,
            odometer_reading=45320,
            price_per_gallon=3.30
        )

        self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=12.2,
            odometer_reading=45650,
            price_per_gallon=3.28
        )

        # Calculate fuel efficiency
        efficiency = self.agent.database.get_vehicle_fuel_efficiency(vehicle_id)

        # Should have calculated efficiency (650 miles / 35.7 gallons ≈ 18.2 MPG)
        self.assertIsNotNone(efficiency)
        self.assertGreater(efficiency, 15.0)
        self.assertLess(efficiency, 25.0)

    def test_vehicle_summary(self):
        """Test comprehensive vehicle summary."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Add some events
        self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=12.0,
            odometer_reading=50000,
            total_cost=39.00
        )

        self.agent.log_maintenance_event(
            vehicle_id=vehicle_id,
            maintenance_type="Oil Change",
            description="Regular maintenance",
            cost=45.99,
            vendor="Quick Lube"
        )

        self.agent.log_repair_event(
            vehicle_id=vehicle_id,
            repair_type="Brake Repair",
            description="Brake pad replacement",
            cost=150.00,
            vendor="Brake Shop"
        )

        # Get vehicle summary
        result = self.agent.get_vehicle_summary(vehicle_id)

        self.assertTrue(result["success"])

        # Check vehicle details
        vehicle = result["vehicle"]
        self.assertEqual(vehicle["make"], "Honda")
        self.assertEqual(vehicle["model"], "Civic")
        self.assertEqual(vehicle["year"], 2020)

        # Check costs
        costs = result["costs"]
        self.assertEqual(costs["fuel"], 39.00)
        self.assertEqual(costs["maintenance"], 45.99)
        self.assertEqual(costs["repair"], 150.00)

        # Check total
        expected_total = 39.00 + 45.99 + 150.00
        self.assertEqual(result["total_operating_costs"], expected_total)

    def test_multi_modal_fuel_event(self):
        """Test fuel event with all multi-modal inputs."""
        # First add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Log fuel event with all multi-modal inputs
        result = self.agent.log_fuel_event(
            vehicle_id=vehicle_id,
            gallons=14.8,
            odometer_reading=51000,
            fuel_type="Diesel",
            price_per_gallon=3.85,
            station_name="Chevron Station #123",
            latitude=34.0522,
            longitude=-118.2437,
            receipt_image_path="/path/to/receipt_image.jpg"
        )

        self.assertTrue(result["success"])

        # Verify data was stored in database
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT fuel_type, gallons, station_name, latitude, longitude, receipt_image_path
                FROM fuel_events WHERE fuel_id = ?
            """, (result["fuel_id"],))
            row = cursor.fetchone()

            self.assertEqual(row[0], "Diesel")
            self.assertEqual(float(row[1]), 14.8)
            self.assertEqual(row[2], "Chevron Station #123")
            self.assertEqual(row[3], 34.0522)
            self.assertEqual(row[4], -118.2437)
            self.assertEqual(row[5], "/path/to/receipt_image.jpg")

    def test_invalid_vehicle_operations(self):
        """Test operations with invalid vehicle IDs."""
        invalid_vehicle_id = "nonexistent-vehicle-id"

        # Test fuel event with invalid vehicle
        fuel_result = self.agent.log_fuel_event(
            vehicle_id=invalid_vehicle_id,
            gallons=10.0,
            odometer_reading=50000
        )
        self.assertFalse(fuel_result["success"])
        self.assertEqual(fuel_result["message"], "Vehicle not found")

        # Test maintenance event with invalid vehicle
        maintenance_result = self.agent.log_maintenance_event(
            vehicle_id=invalid_vehicle_id,
            maintenance_type="Oil Change",
            description="Test",
            cost=50.0,
            vendor="Test Vendor"
        )
        self.assertFalse(maintenance_result["success"])
        self.assertEqual(maintenance_result["message"], "Vehicle not found")

        # Test repair event with invalid vehicle
        repair_result = self.agent.log_repair_event(
            vehicle_id=invalid_vehicle_id,
            repair_type="Brake Repair",
            description="Test",
            cost=100.0,
            vendor="Test Vendor"
        )
        self.assertFalse(repair_result["success"])
        self.assertEqual(repair_result["message"], "Vehicle not found")

    def test_accounting_notification(self):
        """Test accounting notification functionality."""
        test_expense_data = {
            "expense_id": "test-expense-123",
            "vehicle_id": "test-vehicle-456",
            "expense_type": "fuel",
            "amount": 45.50,
            "date": datetime.now().isoformat(),
            "vendor": "Test Station",
            "description": "Test fuel purchase",
            "category": "Vehicle Fuel",
            "tax_deductible": True
        }

        result = self.agent.notify_accounting(test_expense_data)

        self.assertTrue(result["success"])
        self.assertIn("notification_id", result)
        self.assertEqual(result["status"], "sent")

        # Check processed data
        processed = result["processed_data"]
        self.assertEqual(processed["expense_id"], "test-expense-123")
        self.assertEqual(processed["amount"], 45.50)
        self.assertEqual(processed["category"], "Vehicle Fuel")
        self.assertTrue(processed["tax_deductible"])

    def test_available_tools(self):
        """Test that all required tools are available."""
        tools = self.agent.get_available_tools()

        required_tools = [
            "add_vehicle",
            "log_fuel_event",
            "log_maintenance_event",
            "log_repair_event",
            "notify_accounting",
            "get_vehicle_summary"
        ]

        for tool in required_tools:
            self.assertIn(tool, tools, f"Required tool '{tool}' not found")

    def test_database_persistence(self):
        """Test that data persists correctly in database."""
        # Add a vehicle
        vehicle_result = self.agent.add_vehicle(
            vin="1HGCM82633A123456",
            make="Honda",
            model="Civic",
            year=2020,
            license_plate="TEST-001"
        )
        vehicle_id = vehicle_result["vehicle_id"]

        # Create a new agent instance (simulating restart)
        new_agent = FleetManagerAgent(name="NewTestAgent")
        new_agent.database = FleetDatabase(self.test_db_path)

        # Verify vehicle was loaded from database
        self.assertIn(vehicle_id, new_agent.vehicles)
        loaded_vehicle = new_agent.vehicles[vehicle_id]
        self.assertEqual(loaded_vehicle.make, "Honda")
        self.assertEqual(loaded_vehicle.model, "Civic")


def run_comprehensive_demo():
    """Run a comprehensive demonstration of all agent features."""
    print("🧪 Fleet Manager Agent Comprehensive Test Demo")
    print("=" * 60)

    # Create temporary database for demo
    demo_db_fd, demo_db_path = tempfile.mkstemp(suffix='_demo.db')
    os.close(demo_db_fd)

    try:
        # Initialize agent
        agent = FleetManagerAgent(name="DemoAgent")
        agent.database = FleetDatabase(demo_db_path)

        print("✅ Agent initialized with temporary database")

        # Add multiple vehicles
        vehicles = []
        vehicle_data = [
            {"vin": "1HGCM82633A123456", "make": "Honda", "model": "Civic", "year": 2020, "license_plate": "DEMO-001"},
            {"vin": "1FTFW1ET5BFC12345", "make": "Ford", "model": "F-150", "year": 2019, "license_plate": "DEMO-002"},
            {"vin": "1G1YY22G975123456", "make": "Chevrolet", "model": "Camaro", "year": 2021, "license_plate": "DEMO-003"}
        ]

        for vehicle_info in vehicle_data:
            result = agent.add_vehicle(**vehicle_info)
            if result["success"]:
                vehicles.append(result["vehicle_id"])
                print(f"✅ Added {vehicle_info['make']} {vehicle_info['model']}")

        # Log various events for each vehicle
        print("\n📊 Logging various events...")

        for i, vehicle_id in enumerate(vehicles):
            # Fuel events
            agent.log_fuel_event(
                vehicle_id=vehicle_id,
                gallons=12 + i,
                odometer_reading=45000 + (i * 1000),
                fuel_type="Gasoline",
                price_per_gallon=3.25 + (i * 0.10),
                station_name=f"Station {i+1}",
                latitude=40.7128 + i,
                longitude=-74.0060 - i
            )

            # Maintenance events
            agent.log_maintenance_event(
                vehicle_id=vehicle_id,
                maintenance_type="Oil Change",
                description=f"Regular maintenance for vehicle {i+1}",
                cost=45.99 + (i * 5),
                vendor=f"Service Center {i+1}",
                odometer_reading=45000 + (i * 1000)
            )

            # Repair events (every other vehicle)
            if i % 2 == 0:
                agent.log_repair_event(
                    vehicle_id=vehicle_id,
                    repair_type="Brake Service",
                    description=f"Brake repair for vehicle {i+1}",
                    cost=200 + (i * 50),
                    vendor=f"Repair Shop {i+1}",
                    severity="Medium"
                )

        # Generate summaries
        print("\n📋 Vehicle Summaries:")
        for i, vehicle_id in enumerate(vehicles):
            summary = agent.get_vehicle_summary(vehicle_id)
            if summary["success"]:
                v = summary["vehicle"]
                print(f"\n{v['year']} {v['make']} {v['model']} ({v['license_plate']})")
                print(f"  Total Operating Costs: ${summary['total_operating_costs']:.2f}")
                print(f"  - Fuel: ${summary['costs']['fuel']:.2f}")
                print(f"  - Maintenance: ${summary['costs']['maintenance']:.2f}")
                print(f"  - Repairs: ${summary['costs']['repair']:.2f}")

        print(f"\n💾 Demo data saved to: {demo_db_path}")
        print("🎉 Comprehensive demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        # Clean up temporary database
        if os.path.exists(demo_db_path):
            os.unlink(demo_db_path)


if __name__ == "__main__":
    # Run unit tests
    print("Running Fleet Manager Agent Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    print("\n" + "="*60)

    # Run comprehensive demo
    run_comprehensive_demo()