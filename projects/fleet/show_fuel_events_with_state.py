#!/usr/bin/env python3
"""
Comprehensive Fuel Events Display with Vehicle State

Shows all fuel events along with:
- Vehicle state at the time of each fuel event
- MPG calculations since last fuel event
- Running average MPG
- Current vehicle mileage updates
"""

import sys
import os

# Add the parent directory to the path to import the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import FleetManagerAgent


def main():
    """Display comprehensive fuel events with vehicle state and MPG calculations."""
    print("🚛 COMPREHENSIVE FUEL EVENTS WITH VEHICLE STATE")
    print("=" * 70)

    # Initialize the agent
    agent = FleetManagerAgent(name="FuelEventsDisplay")

    # Get all vehicle IDs
    vehicle_ids = list(agent.vehicles.keys())

    if not vehicle_ids:
        print("❌ No vehicles found in database")
        return

    print(f"📊 Found {len(vehicle_ids)} vehicle(s) in fleet")
    print()

    for vehicle_id in vehicle_ids:
        vehicle = agent.vehicles[vehicle_id]
        print(f"🚗 VEHICLE: {vehicle.year} {vehicle.make} {vehicle.model}")
        print(f"   📋 VIN: {vehicle.vin}")
        print(f"   🏷️  License: {vehicle.license_plate}")
        print(f"   🎨 Color: {vehicle.color}")
        print(f"   🔧 Engine: {vehicle.engine_type}")
        print()

        # Get all fuel events for this vehicle
        fuel_events = agent.database.get_vehicle_fuel_events(vehicle_id)

        if not fuel_events:
            print("   ⛽ No fuel events found for this vehicle")
            print()
            continue

        print(f"   ⛽ FUEL EVENTS ({len(fuel_events)} total):")
        print("   " + "-" * 60)

        # Update vehicle mileage to the latest odometer reading
        latest_mileage = max(event['odometer_reading'] for event in fuel_events)
        agent.update_vehicle_mileage(vehicle_id, latest_mileage)
        print(f"   📊 Updated vehicle mileage to: {latest_mileage:,} miles")
        print()

        # Display each fuel event with calculations
        for i, event in enumerate(fuel_events, 1):
            fuel_id = event['fuel_id']

            print(f"   🔢 Event #{i}: {fuel_id[:8]}...")
            print(f"      📅 Date: {event['date_time']}")
            print(f"      🛣️  Odometer: {event['odometer_reading']:,} miles")
            print(f"      ⛽ Fuel: {event['gallons']} gallons @ ${event['price_per_gallon']:.2f}/gal")
            print(f"      💰 Total Cost: ${event['total_cost']:.2f}")

            if event['station_name']:
                location_info = event['station_name']
                if event['latitude'] and event['longitude']:
                    location_info += f" ({event['latitude']:.4f}, {event['longitude']:.4f})"
                print(f"      📍 Location: {location_info}")

            if event['receipt_image_path']:
                print(f"      📸 Receipt: {event['receipt_image_path']}")

            # Calculate MPG since last fuel event
            mpg_result = agent.calculate_mpg_since_last_fuel(vehicle_id, fuel_id)
            if mpg_result["success"]:
                mpg_data = mpg_result
                print(f"      📈 MPG since last: {mpg_data['mpg_since_last']:.1f} MPG")
                print(f"         ({mpg_data['miles_driven']} miles ÷ {mpg_data['gallons_used']} gallons)")
            else:
                print(f"      📈 MPG since last: {mpg_result['message']}")

            print()

        # Calculate and display running average MPG
        running_mpg_result = agent.calculate_running_mpg(vehicle_id)
        if running_mpg_result["success"]:
            mpg_data = running_mpg_result
            print(f"   📊 RUNNING AVERAGE MPG: {mpg_data['running_average_mpg']:.1f} MPG")
            print(f"      📏 Total Distance: {mpg_data['total_miles_driven']:,} miles")
            print(f"      ⛽ Total Fuel Used: {mpg_data['total_gallons_used']:.1f} gallons")
            print(f"      🔢 Fuel Events: {mpg_data['fuel_events_count']}")
            print(f"      📊 Odometer Range: {mpg_data['odometer_range']['first']:,} - {mpg_data['odometer_range']['last']:,} miles")
        else:
            print(f"   📊 Running MPG: {running_mpg_result['message']}")

        # Get comprehensive vehicle summary
        summary = agent.get_vehicle_summary(vehicle_id)
        if summary["success"]:
            costs = summary["costs"]
            print(f"\n   💰 OPERATING COSTS:")
            print(f"      ⛽ Fuel: ${costs['fuel']:.2f}")
            print(f"      🔧 Maintenance: ${costs['maintenance']:.2f}")
            print(f"      🛠️  Repairs: ${costs['repair']:.2f}")
            print(f"      📊 Total: ${summary['total_operating_costs']:.2f}")

        print("\n" + "=" * 70)
        print()

    # Display fleet-wide statistics
    print("🏢 FLEET SUMMARY:")
    total_vehicles = len(vehicle_ids)
    total_fuel_events = sum(len(agent.database.get_vehicle_fuel_events(vid)) for vid in vehicle_ids)
    total_costs = sum(agent.get_vehicle_summary(vid)["total_operating_costs"]
                     for vid in vehicle_ids if agent.get_vehicle_summary(vid)["success"])

    print(f"   🚗 Total Vehicles: {total_vehicles}")
    print(f"   ⛽ Total Fuel Events: {total_fuel_events}")
    print(f"   💰 Total Fleet Operating Costs: ${total_costs:.2f}")

    # Show tools used
    print(f"\n🛠️  TOOLS DEMONSTRATED:")
    tools_used = [
        "update_vehicle_mileage",
        "calculate_mpg_since_last_fuel",
        "calculate_running_mpg",
        "get_vehicle_summary"
    ]
    for tool in tools_used:
        print(f"   ✅ {tool}")

    print(f"\n🎉 Comprehensive fuel events display completed!")


if __name__ == "__main__":
    main()