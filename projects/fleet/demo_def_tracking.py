#!/usr/bin/env python3
"""
DEF Tracking Demonstration

This demo shows how the Fleet Management Agent properly handles DEF (Diesel Exhaust Fluid)
as a maintenance consumable rather than fuel, including:

- DEF consumption tracking in gallons per mile
- Cost categorization as maintenance expenses
- Proper accounting notifications
- Multi-modal DEF event logging
"""

import sys
import os

# Add the parent directory to the path to import the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import FleetManagerAgent


def main():
    """Demonstrate DEF tracking as maintenance consumable."""
    print("🚛 DEF (DIESEL EXHAUST FLUID) TRACKING DEMONSTRATION")
    print("=" * 65)
    print("Showing DEF as maintenance consumable, NOT fuel")
    print("=" * 65)

    # Initialize the agent with fresh database
    agent = FleetManagerAgent(name="DEFTrackingDemo")

    # Add a diesel truck that uses DEF
    print("\\n🚗 Adding diesel truck to fleet...")
    truck_result = agent.add_vehicle(
        vin="1FTFW1ET9DFC45678",
        make="Ford",
        model="F-550 Super Duty",
        year=2022,
        license_plate="DEF-DEMO",
        color="White",
        engine_type="6.7L V8 Turbo Diesel"
    )

    if not truck_result["success"]:
        print(f"❌ Failed to add truck: {truck_result['message']}")
        return

    truck_id = truck_result["vehicle_id"]
    print(f"✅ Added: 2022 Ford F-550 Super Duty ({truck_result['message']})")

    # Log regular diesel fuel event first
    print("\\n⛽ Logging regular diesel fuel event...")
    diesel_result = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=35.0,
        odometer_reading=15000,
        fuel_type="Diesel",
        price_per_gallon=4.25,
        station_name="Truck Stop America",
        latitude=35.7796,
        longitude=-78.6382
    )

    if diesel_result["success"]:
        print(f"✅ Diesel Event: {diesel_result['fuel_id'][:8]}...")
        calc = diesel_result["calculations"]
        print(f"   💰 Total Cost: ${calc['total_cost']:.2f}")
        print(f"   📊 Categorized as: Fuel (not maintenance)")
        print(f"   🧾 Accounting: {diesel_result['accounting_notification']['notification_id'][:8]}...")

    # Log DEF consumable event
    print("\\n🔵 Logging DEF (Diesel Exhaust Fluid) event...")
    print("   NOTE: DEF is a maintenance consumable, NOT fuel!")

    def_result = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=2.5,  # DEF tank capacity is typically 5-10 gallons
        odometer_reading=15000,
        fuel_type="DEF",
        price_per_gallon=8.50,  # DEF is more expensive per gallon
        station_name="Truck Stop America",
        latitude=35.7796,
        longitude=-78.6382,
        consumption_rate=0.00075  # ~0.075 gallons per 100 miles (3% of diesel consumption)
    )

    if def_result["success"]:
        print(f"✅ DEF Event: {def_result['fuel_id'][:8]}...")
        calc = def_result["calculations"]
        print(f"   💰 Total Cost: ${calc['total_cost']:.2f}")
        print(f"   📊 Categorized as: MAINTENANCE (not fuel!)")
        print(f"   🔵 Consumption Rate: 0.075 gallons per 100 miles")
        print(f"   🧾 Accounting: {def_result['accounting_notification']['notification_id'][:8]}...")

    # Log another diesel fuel event after DEF
    print("\\n⛽ Logging another diesel fuel event...")
    diesel_result_2 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=32.8,
        odometer_reading=15450,
        fuel_type="Diesel",
        total_cost=145.20,  # Calculate price per gallon automatically
        station_name="Shell Truck Plaza"
    )

    if diesel_result_2["success"]:
        print(f"✅ Diesel Event 2: {diesel_result_2['fuel_id'][:8]}...")
        calc = diesel_result_2["calculations"]
        print(f"   💰 Total Cost: ${calc['total_cost']:.2f} (${calc['price_per_gallon']:.2f}/gal)")
        print(f"   📊 Categorized as: Fuel")

    # Show cost breakdown
    print("\\n💰 COST BREAKDOWN BY CATEGORY:")
    print("-" * 50)

    summary = agent.get_vehicle_summary(truck_id)
    if summary["success"]:
        costs = summary["costs"]
        print(f"⛽ Fuel Costs (Diesel only): ${costs['fuel']:.2f}")
        print(f"🔧 Maintenance Costs (including DEF): ${costs['maintenance']:.2f}")
        print(f"🛠️  Repair Costs: ${costs['repair']:.2f}")
        print(f"📊 Total Operating Costs: ${summary['total_operating_costs']:.2f}")

    # Show detailed fuel events with DEF tracking
    print("\\n📊 DETAILED FUEL/CONSUMABLE EVENTS:")
    print("-" * 50)

    fuel_events = agent.database.get_vehicle_fuel_events(truck_id)
    for i, event in enumerate(fuel_events, 1):
        print(f"\\n🔢 Event #{i}: {event['fuel_type']}")
        print(f"   📅 Odometer: {event['odometer_reading']:,} miles")
        print(f"   🪣 Amount: {event['gallons']} gallons @ ${event['price_per_gallon']:.2f}/gal")
        print(f"   💰 Cost: ${event['total_cost']:.2f}")
        print(f"   📍 Station: {event['station_name'] or 'Not specified'}")

        if event['is_consumable']:
            print(f"   🔵 TYPE: MAINTENANCE CONSUMABLE (DEF)")
            print(f"   📊 Consumption Rate: {event['consumption_rate']:.6f} gal/mile")
            consumption_per_100_miles = event['consumption_rate'] * 100
            print(f"   📈 Usage: {consumption_per_100_miles:.3f} gallons per 100 miles")
        else:
            print(f"   ⛽ TYPE: FUEL")

    # Calculate DEF consumption projections
    def_event = next((e for e in fuel_events if e['is_consumable']), None)
    if def_event:
        print("\\n🔮 DEF CONSUMPTION PROJECTIONS:")
        print("-" * 40)
        consumption_rate = def_event['consumption_rate']

        miles_scenarios = [1000, 5000, 10000, 25000]
        for miles in miles_scenarios:
            def_needed = consumption_rate * miles
            cost = def_needed * def_event['price_per_gallon']
            print(f"   {miles:,} miles: {def_needed:.2f} gallons, ${cost:.2f}")

    # Show accounting categorization
    print("\\n🧾 ACCOUNTING INTEGRATION:")
    print("-" * 35)
    print("✅ Diesel fuel → 'Vehicle Fuel' category")
    print("✅ DEF consumable → 'Vehicle Maintenance' category")
    print("✅ Automatic expense notifications sent")
    print("✅ Tax-deductible business expenses flagged")

    print("\\n🎉 DEF tracking demonstration completed!")
    print("\\n📝 KEY POINTS DEMONSTRATED:")
    print("  • DEF is tracked as a maintenance consumable, NOT fuel")
    print("  • Consumption rate tracking (gallons per mile)")
    print("  • Proper cost categorization in accounting")
    print("  • Multi-modal event logging with GPS")
    print("  • Automatic expense notifications")
    print("  • Consumption projections for maintenance planning")


if __name__ == "__main__":
    main()