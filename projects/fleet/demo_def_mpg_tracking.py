#!/usr/bin/env python3
"""
DEF MPG Tracking Demonstration

This demo shows DEF being tracked in MPG (like fuel) but categorized as maintenance costs.

DEF consumption is typically:
- ~3% of diesel fuel consumption by volume
- If diesel gets 13 MPG, DEF might get ~433 MPG (13 ÷ 0.03)
"""

import sys
import os

# Add the parent directory to the path to import the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import FleetManagerAgent


def main():
    """Demonstrate DEF tracked in MPG but categorized as maintenance."""
    print("🔵 DEF MPG TRACKING DEMONSTRATION")
    print("=" * 50)
    print("DEF tracked in MPG (like fuel) but categorized as maintenance")
    print("=" * 50)

    # Initialize the agent with fresh database
    agent = FleetManagerAgent(name="DEFMPGDemo")

    # Add a diesel truck that uses DEF
    print("\\n🚗 Adding diesel truck to fleet...")
    truck_result = agent.add_vehicle(
        vin="1FTFW1ET9DFC99999",
        make="Ford",
        model="F-450 Super Duty",
        year=2024,
        license_plate="DEF-MPG",
        color="Blue",
        engine_type="6.7L V8 Turbo Diesel"
    )

    truck_id = truck_result["vehicle_id"]
    print(f"✅ Added: 2024 Ford F-450 Super Duty")

    # Log diesel fuel events for comparison
    print("\\n⛽ Logging diesel fuel events...")

    diesel1 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=28.0,
        odometer_reading=75000,
        fuel_type="Diesel",
        price_per_gallon=4.20,
        station_name="Pilot Travel Center"
    )
    print(f"✅ Diesel #1: 28.0 gallons @ $4.20/gal = ${diesel1['calculations']['total_cost']:.2f}")

    # Second diesel fill for MPG calculation
    diesel2 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=30.2,
        odometer_reading=75390,
        fuel_type="Diesel",
        price_per_gallon=4.18,
        station_name="Flying J"
    )
    print(f"✅ Diesel #2: 30.2 gallons @ $4.18/gal = ${diesel2['calculations']['total_cost']:.2f}")

    # Calculate diesel MPG
    diesel_mpg = agent.calculate_mpg_since_last_fuel(truck_id, diesel2['fuel_id'])
    if diesel_mpg["success"]:
        print(f"   📈 Diesel MPG: {diesel_mpg['mpg_since_last']:.1f} MPG")

    # Log first DEF event
    print("\\n🔵 Logging DEF events (tracked in MPG like fuel)...")
    def1 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=1.2,  # Much smaller amounts than diesel
        odometer_reading=75390,
        fuel_type="DEF",
        price_per_gallon=8.50,
        station_name="Flying J"
    )
    print(f"✅ DEF #1: 1.2 gallons @ $8.50/gal = ${def1['calculations']['total_cost']:.2f}")

    # More driving, then second DEF event
    diesel3 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=29.5,
        odometer_reading=75780,
        fuel_type="Diesel",
        price_per_gallon=4.25,
        station_name="Shell"
    )
    print(f"\\n⛽ Diesel #3: 29.5 gallons @ $4.25/gal = ${diesel3['calculations']['total_cost']:.2f}")

    # Second DEF event
    def2 = agent.log_fuel_event(
        vehicle_id=truck_id,
        gallons=1.0,
        odometer_reading=75780,
        fuel_type="DEF",
        price_per_gallon=8.50,
        station_name="Shell"
    )
    print(f"🔵 DEF #2: 1.0 gallons @ $8.50/gal = ${def2['calculations']['total_cost']:.2f}")

    # Calculate DEF MPG
    def_mpg = agent.calculate_mpg_since_last_fuel(truck_id, def2['fuel_id'])
    if def_mpg["success"]:
        print(f"   📈 DEF MPG: {def_mpg['mpg_since_last']:.0f} MPG (very high because DEF usage is low)")
        print(f"       ({def_mpg['miles_driven']} miles ÷ {def_mpg['gallons_used']} gallons)")

    # Show cost categorization
    print("\\n💰 COST BREAKDOWN BY CATEGORY:")
    print("-" * 50)

    summary = agent.get_vehicle_summary(truck_id)
    if summary["success"]:
        costs = summary["costs"]
        print(f"⛽ Fuel Costs (Diesel only): ${costs['fuel']:.2f}")
        print(f"🔧 Maintenance Costs (including DEF): ${costs['maintenance']:.2f}")
        print(f"📊 Total Operating Costs: ${summary['total_operating_costs']:.2f}")

    # Show all events with their tracking methods
    print("\\n📊 ALL EVENTS WITH TRACKING METHODS:")
    print("-" * 50)

    fuel_events = agent.database.get_vehicle_fuel_events(truck_id)

    for i, event in enumerate(fuel_events, 1):
        print(f"\\n🔢 Event #{i}: {event['fuel_type']}")
        print(f"   📅 Odometer: {event['odometer_reading']:,} miles")
        print(f"   🪣 Amount: {event['gallons']} gallons @ ${event['price_per_gallon']:.2f}/gal")
        print(f"   💰 Cost: ${event['total_cost']:.2f}")

        if event['fuel_type'] == 'DEF':
            print(f"   🔵 TRACKING: MPG (like fuel)")
            print(f"   📂 CATEGORY: Maintenance")
            print(f"   💡 NOTE: DEF gets very high 'MPG' because usage is low")
        else:
            print(f"   ⛽ TRACKING: MPG")
            print(f"   📂 CATEGORY: Fuel")

    # Calculate running averages for both diesel and DEF
    print("\\n📈 RUNNING EFFICIENCY CALCULATIONS:")
    print("-" * 45)

    # Get running MPG for diesel (fuel events only)
    diesel_running = agent.calculate_running_mpg(truck_id)
    if diesel_running["success"]:
        # This includes all fuel events, so we need to separate manually
        diesel_total_gallons = sum(e['gallons'] for e in fuel_events if e['fuel_type'] == 'Diesel')
        def_total_gallons = sum(e['gallons'] for e in fuel_events if e['fuel_type'] == 'DEF')

        total_miles = diesel_running['total_miles_driven']

        diesel_mpg = total_miles / diesel_total_gallons if diesel_total_gallons > 0 else 0
        def_mpg = total_miles / def_total_gallons if def_total_gallons > 0 else 0

        print(f"⛽ Diesel Running MPG: {diesel_mpg:.1f} MPG")
        print(f"🔵 DEF Running MPG: {def_mpg:.0f} MPG")
        print(f"📏 Total Miles: {total_miles:,} miles")
        print(f"📊 Diesel Used: {diesel_total_gallons} gallons")
        print(f"📊 DEF Used: {def_total_gallons} gallons")

        # Show DEF as percentage of diesel consumption
        if diesel_total_gallons > 0:
            def_percentage = (def_total_gallons / diesel_total_gallons) * 100
            print(f"📈 DEF is {def_percentage:.1f}% of diesel consumption by volume")

    print(f"\\n🎉 DEF MPG tracking demonstration completed!")
    print(f"\\n📝 KEY POINTS DEMONSTRATED:")
    print(f"  ✅ DEF tracked in MPG just like fuel")
    print(f"  ✅ DEF categorized as maintenance costs (not fuel costs)")
    print(f"  ✅ DEF gets very high 'MPG' because consumption is low")
    print(f"  ✅ Both diesel and DEF use same tracking method (MPG)")
    print(f"  ✅ Different cost categorization based on type")


if __name__ == "__main__":
    main()