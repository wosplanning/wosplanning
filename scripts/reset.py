#!/usr/bin/env python3

import os
import json
import argparse
from datetime import datetime
import subprocess


def confirm_database_deletion(db_path="database/production.db"):
    """Ask for confirmation before deleting the database"""

    if not os.path.exists(db_path):
        print(f"ℹ️  Database file does not exist: {db_path}")
        return True

    print(f"⚠️  WARNING: This will permanently delete the SQLite database file:")
    print(f"   {os.path.abspath(db_path)}")

    while True:
        response = input("\nDo you want to delete the database file? (y/N): ").strip().lower()

        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("❌ Please enter 'y' for yes or 'n' for no.")


def remove_and_create_db(db_path="database/production.db"):
    """Remove existing database file and create a fresh one using touch"""

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✅ Removed existing database: {db_path}")

    try:
        subprocess.run(["touch", db_path], check=True)
        print(f"✅ Created fresh database: {db_path}")
    except subprocess.CalledProcessError:
        with open(db_path, 'w') as _:
            pass
        print(f"✅ Created fresh database: {db_path} (fallback method)")


def confirm_svs_dates_reset():
    """Ask for confirmation about SVS dates - reset to empty or input new data"""
    print("\n" + "=" * 50)
    print("SVS DATES CONFIGURATION")
    print("=" * 50)

    print("Choose an option for SVS dates:")
    print("1. Reset to empty list (clear all dates)")
    print("2. Input new date data")

    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()

        if choice == '1':
            return 'reset'
        elif choice == '2':
            return 'input'
        else:
            print("❌ Please enter '1' for reset or '2' for input.")


def create_empty_svs_dates(json_path="database/svs_dates.json"):
    """Create an empty SVS dates JSON file"""

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        print(f"✅ Created empty SVS dates file: {json_path}")
        return json_path
    except Exception as e:
        print(f"❌ Error creating empty JSON file: {e}")
        return None


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


def save_to_json(events_list, json_path="database/svs_dates.json"):
    """Save events list to JSON file in database directory"""

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(events_list, f, indent=4, ensure_ascii=False)
        print(f"✅ Data saved successfully to: {json_path}")
        return json_path
    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")
        return None


def display_summary(events_list, json_path):
    """Display a summary of collected data"""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if not events_list:
        print("📝 SVS dates list is empty")
    else:
        for event in events_list:
            print(f"📅 {event['date']} - {event['minister']}: {event['type']}")

    if json_path:
        print(f"\n💾 Data saved to: {json_path}")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Database reset and SVS dates collection script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                                    # Use default paths
  %(prog)s --json-file custom_dates.json                     # Use custom JSON file
  %(prog)s --db-file data/custom.db                          # Use custom database file
  %(prog)s -j data/events.json -d data/app.db                # Use custom paths for both
        """
    )

    parser.add_argument(
        '--json-file', '-j',
        default='database/svs_dates.json',
        help='Path to JSON file for SVS dates (default: database/svs_dates.json)'
    )

    parser.add_argument(
        '--db-file', '-d',
        default='database/production.db',
        help='Path to SQLite database file (default: database/production.db)'
    )

    return parser.parse_args()


def main():
    """Main function to orchestrate the script"""
    # Parse command line arguments
    args = parse_arguments()
    json_file_path = args.json_file
    db_file_path = args.db_file

    print("🗄️  DATABASE RESET AND DATE COLLECTION SCRIPT")
    print("=" * 60)
    print(f"🗄️  Database file path: {db_file_path}")
    print(f"📁 JSON file path: {json_file_path}")

    try:
        # Step 1: Confirm database deletion
        print("\n1️⃣  Database deletion confirmation...")
        if confirm_database_deletion(db_file_path):
            print(f"\n🔄 Resetting database at {db_file_path}...")
            remove_and_create_db(db_file_path)
        else:
            print("\n⏭️  Skipping database deletion.")

        # Step 2: Confirm SVS dates action
        print("\n2️⃣  SVS dates configuration...")
        svs_action = confirm_svs_dates_reset()

        events_list = []
        json_path = None

        if svs_action == 'reset':
            print(f"\n🔄 Resetting SVS dates to empty list in {json_file_path}...")
            json_path = create_empty_svs_dates(json_file_path)
        else:  # svs_action == 'input'
            print("\n📝 Collecting event dates...")
            events_list = collect_dates()
            print(f"\n3️⃣  Saving data to {json_file_path}...")
            json_path = save_to_json(events_list, json_file_path)

        # Step 3: Display summary
        display_summary(events_list, json_path)

        print("\n🎉 Script completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    main()