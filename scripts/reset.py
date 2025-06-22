#!/usr/bin/env python3

import os
import json
from datetime import datetime
import subprocess


def remove_and_create_db():
    """Remove existing database file and create a fresh one using touch"""
    db_path = "database/production.db"

    os.makedirs("database", exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)

        print(f"Removed existing database: {db_path}")

    try:
        subprocess.run(["touch", db_path], check=True)

        print(f"Created fresh database: {db_path}")
    except subprocess.CalledProcessError:
        with open(db_path, 'w') as _:
            pass

        print(f"Created fresh database: {db_path} (fallback method)")


def get_date_input(prompt):
    """Get date input from user with validation"""
    today = datetime.now().date()

    while True:
        date_str = input(f"{prompt} (YYYY-MM-DD): ").strip()

        if not date_str:
            print("❌ Date cannot be empty. Please try again.")
            continue

        try:
            input_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            if input_date < today:
                print(f"❌ Date {date_str} is in the past. Please enter a future date (today is {today}).")
                continue

            print(f"✅ Valid date: {date_str}")
            return date_str

        except ValueError:
            print("❌ Invalid date format or invalid date. Please use YYYY-MM-DD format (e.g., 2025-06-16).")
            print("   Make sure the date actually exists (valid month/day combination).")


def collect_dates():
    """Collect dates for each position/event interactively"""
    print("\n" + "=" * 50)
    print("COLLECTING EVENT DATES")
    print("=" * 50)

    events_list = []

    events = [
        ("Vice President", "Construction Day"),
        ("Vice President", "Research Day"),
        ("Minister of Education", "Training Day")
    ]

    for minister, event_type in events:
        print(f"\n📅 {minister} - {event_type}")
        date = get_date_input(f"Enter date for {minister} - {event_type}")

        event_obj = {
            "date": date,
            "type": event_type,
            "minister": minister
        }
        events_list.append(event_obj)
        print(f"✅ Saved: {minister} - {event_type} = {date}")

    return events_list


def save_to_json(events_list):
    """Save events list to JSON file in database directory"""
    json_path = "database/svs_dates.json"

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(events_list, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Data saved successfully to: {json_path}")
        return json_path
    except Exception as e:
        print(f"\n❌ Error saving JSON file: {e}")
        return None


def display_summary(events_list, json_path):
    """Display a summary of collected data"""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    for event in events_list:
        print(f"📅 {event['date']} - {event['minister']}: {event['type']}")

    if json_path:
        print(f"\n💾 Data saved to: {json_path}")


def main():
    """Main function to orchestrate the script"""
    print("🗄️  DATABASE RESET AND DATE COLLECTION SCRIPT")
    print("=" * 60)

    try:
        # Step 1: Remove old database and create fresh one
        print("\n1️⃣  Resetting database...")
        remove_and_create_db()

        # Step 2: Collect dates interactively
        print("\n2️⃣  Collecting event dates...")
        events_list = collect_dates()

        # Step 3: Save to JSON
        print("\n3️⃣  Saving data...")
        json_path = save_to_json(events_list)

        # Step 4: Display summary
        display_summary(events_list, json_path)

        print("\n🎉 Script completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    main()