# Fleet Management Agent

A comprehensive Fleet Management Agent for the LiMOS system using the Anthropic SDK.

## 🚛 Overview

The Fleet Management Agent provides complete vehicle operational record management including:

- **Vehicle Details**: VIN, make, model, year, license plate, color, engine type
- **Insurance Records**: Policy tracking with provider, coverage, and expiration management
- **Maintenance Logs**: Service tracking with parts replacement and scheduling
- **Repair Events**: Repair tracking with warranty information and severity levels
- **Fuel Events**: Multi-modal fuel logging with GPS, receipts, and automatic calculations
- **Cost Analytics**: Fuel efficiency, cost per mile, and comprehensive expense tracking
- **Accounting Integration**: Automatic expense notifications for business accounting

## 🔧 Features

### ✅ All Required Functionality Implemented

- **Vehicle Management**: Add vehicles with complete details (VIN, make, model, year, license plate)
- **Multi-Modal Fuel Events**: Support for numeric data, text descriptions, GPS coordinates, and receipt images
- **Automatic Calculations**: Cost per mile, fuel efficiency (MPG), price per gallon calculations
- **Database Persistence**: SQLite database with proper foreign key relationships
- **Accounting Notifications**: Automatic expense categorization and tax-deductible flagging
- **Tool Decorators**: All functions properly decorated with `@tool` for method discovery

### 🛠️ Agent Tools

- `add_vehicle()` - Add new vehicles to the fleet
- `log_fuel_event()` - Log fuel purchases with multi-modal inputs
- `log_maintenance_event()` - Track maintenance with parts and scheduling
- `log_repair_event()` - Log repairs with warranty and severity tracking
- `notify_accounting()` - Send expense data to accounting system
- `get_vehicle_summary()` - Generate comprehensive vehicle reports

## 🚀 Quick Start

### Basic Usage

```python
from agents import FleetManagerAgent

# Initialize the agent
agent = FleetManagerAgent(name="MyFleetManager")

# Add a vehicle
vehicle_result = agent.add_vehicle(
    vin="1HGCM82633A123456",
    make="Honda",
    model="Civic",
    year=2020,
    license_plate="ABC-1234",
    color="Blue",
    engine_type="4-Cylinder"
)

vehicle_id = vehicle_result["vehicle_id"]

# Log a fuel event with GPS and receipt
fuel_result = agent.log_fuel_event(
    vehicle_id=vehicle_id,
    gallons=12.5,
    odometer_reading=45000,
    price_per_gallon=3.25,
    station_name="Shell Station",
    latitude=40.7128,
    longitude=-74.0060,
    receipt_image_path="/path/to/receipt.jpg"
)

# Log maintenance
maintenance_result = agent.log_maintenance_event(
    vehicle_id=vehicle_id,
    maintenance_type="Oil Change",
    description="Regular oil change and filter replacement",
    cost=45.99,
    vendor="Quick Lube Plus",
    next_service_due=48000,
    parts_replaced=["Oil Filter", "Engine Oil"]
)

# Get comprehensive vehicle summary
summary = agent.get_vehicle_summary(vehicle_id)
print(f"Total operating costs: ${summary['total_operating_costs']:.2f}")
print(f"Fuel efficiency: {summary['fuel_efficiency_mpg']:.1f} MPG")
```

### Running the Demo

```bash
# Run the comprehensive demonstration
cd projects/fleet
python demo_fleet_agent.py

# Run DEF tracking demonstration
python demo_def_mpg_tracking.py

# Run combined fuel and DEF tracking
python demo_combined_fuel_and_def.py

# Show fuel events with vehicle state and MPG calculations
python show_fuel_events_with_state.py

# Run the basic example
python agents/fleet_manager_agent_compatible.py
```

## 📊 Data Models

### Vehicle Information
- Vehicle ID, VIN, Make, Model, Year
- License plate, Color, Engine type
- Creation and update timestamps

### Fuel Events (Multi-Modal Support)
- **Numeric**: Gallons, odometer reading, costs
- **Text**: Station name, fuel type, descriptions
- **Location**: GPS coordinates (latitude, longitude)
- **Images**: Receipt image file paths
- **Calculations**: Automatic price per gallon ↔ total cost conversion
- **DEF Tracking**: DEF (Diesel Exhaust Fluid) tracked in MPG but categorized as maintenance
- **Fuel Types**: Gasoline, Diesel, E85, Biodiesel (fuel costs), DEF (maintenance costs)

### Maintenance Events
- Maintenance type, description, cost
- Vendor information and scheduling
- Parts replaced tracking
- Next service due calculations

### Repair Events
- Repair type, description, cost
- Warranty information tracking
- Severity levels (Low, Medium, High, Critical)
- Vendor and completion details

## 💾 Database Schema

SQLite database with the following tables:

- `vehicles` - Vehicle master records
- `fuel_events` - Fuel purchase tracking with GPS
- `maintenance_events` - Service and maintenance logs
- `repair_events` - Repair tracking with warranty info

All tables include proper foreign key relationships and indexing for performance.

## 🧾 Accounting Integration

The agent automatically notifies an accounting system for all expenses:

```python
# Automatic accounting notification for all events
{
    "expense_id": "unique-id",
    "vehicle_id": "vehicle-reference",
    "expense_type": "fuel|maintenance|repair",
    "amount": 45.99,
    "date": "2025-01-15T10:30:00Z",
    "vendor": "Service Provider",
    "description": "Detailed description",
    "category": "Vehicle Expenses",
    "tax_deductible": true
}
```

## 📈 Cost Analytics

### Automatic Calculations
- **Fuel Efficiency**: MPG calculations from multiple fuel events
- **DEF Efficiency**: MPG calculations for DEF consumption (typically 200-500 MPG)
- **Cost Per Mile**: Maintenance and repair cost analysis
- **Total Operating Costs**: Comprehensive expense tracking by category
- **Price Validation**: Automatic cost cross-calculations

### DEF (Diesel Exhaust Fluid) Tracking
- **Tracking Method**: MPG calculations (same as fuel)
- **Cost Category**: Maintenance expenses (not fuel expenses)
- **Typical Consumption**: 2-5% of diesel fuel volume
- **Expected MPG**: 200-500 MPG (very high due to low consumption)
- **Accounting**: Automatically categorized as maintenance for tax purposes

### Reporting Features
- Vehicle-specific cost breakdowns
- Fleet-wide expense summaries
- Fuel efficiency trends (diesel and DEF separate)
- Maintenance scheduling alerts
- DEF consumption projections

## 🏗️ Architecture

The Fleet Management Agent is available in two implementations:

1. **LiMOS BaseAgent Integration** (`fleet_manager_agent.py`):
   - Uses the LiMOS `BaseAgent` framework
   - Async/await architecture
   - Full lifecycle management and metrics
   - Integrated with LiMOS agent registry

2. **Standalone Compatible Version** (`fleet_manager_agent_compatible.py`):
   - Independent implementation
   - No external framework dependencies
   - Simple tool discovery pattern
   - Easy to deploy standalone

```python
# LiMOS BaseAgent version
from core.agents.base import BaseAgent, AgentConfig
class FleetManagerAgent(BaseAgent):
    async def _execute(self, input_data, **kwargs):
        # Agent operations

# Standalone version
from agents.fleet_manager_agent_compatible import BaseAgent, tool
class FleetManagerAgent(BaseAgent):
    @tool
    def log_fuel_event(self, ...):
        # Direct method invocation
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd projects/fleet
python tests/test_fleet_manager_agent.py
```

Tests cover:
- Vehicle management operations
- Multi-modal fuel event logging
- Maintenance and repair tracking
- Cost calculations and analytics
- Database persistence
- Accounting notifications
- Error handling and validation

## 📁 Project Structure

```
projects/fleet/
├── agents/
│   ├── __init__.py
│   ├── fleet_manager_agent.py                # LiMOS BaseAgent version
│   └── fleet_manager_agent_compatible.py    # Standalone version
├── tests/
│   └── test_fleet_manager_agent.py          # Comprehensive test suite
├── demo_fleet_agent.py                      # Full demonstration
├── README.md                               # This file
└── fleet_management.db                     # SQLite database (auto-created)
```

## 🔮 Future Enhancements

Planned improvements:

1. **Enhanced AI Integration**: Advanced analysis and predictions using Claude
2. **Real-time Processing**: Live data streaming and alerts
3. **Advanced Analytics**: Machine learning for maintenance prediction
4. **Mobile Integration**: Mobile app support for field operations
5. **API Gateway**: RESTful API for external integrations

## 📞 Support

For issues or questions about the Fleet Management Agent:

1. Check the test examples for expected behavior
2. Review the demo script for usage patterns
3. Examine the database schema for data relationships
4. Test with the comprehensive demo for full functionality verification

---

**Status**: ✅ **Production Ready** - All requirements implemented and tested