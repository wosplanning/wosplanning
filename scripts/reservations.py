#!/usr/bin/env python3

import argparse
import random
import os
import sqlite3
import sys
import time
from datetime import datetime
from typing import List, Tuple, Optional


class ReservationManager:
    def __init__(self, db_path: str = "database/production.db"):
        """Initialize the reservation manager with database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.max_retries = 3
        self.retry_delay_range = (0.1, 0.5)

    def execute_with_retry(self, query: str, params: Tuple = None, fetch_method: str = None, max_retries: int = None):
        """Execute a query with retry logic for handling database locks."""
        if max_retries is None:
            max_retries = self.max_retries

        last_exception = None

        for attempt in range(max_retries):
            try:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                if fetch_method == "fetchone":
                    return self.cursor.fetchone()
                elif fetch_method == "fetchall":
                    return self.cursor.fetchall()
                elif fetch_method == "rowcount":
                    return self.cursor.rowcount
                else:
                    return True

            except sqlite3.OperationalError as e:
                last_exception = e
                error_msg = str(e).lower()

                if "database is locked" in error_msg or "database is busy" in error_msg:
                    if attempt < max_retries - 1:
                        delay = random.uniform(*self.retry_delay_range)
                        print(
                            f"Database is busy, retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"Database remained locked after {max_retries} attempts.")
                        raise
                else:
                    # For other SQLite errors, don't retry
                    raise
            except Exception as _:
                # For non-SQLite errors, don't retry
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception

    def connect(self):
        """Establish database connection with WAL mode for better concurrency."""
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=30.0)
            self.cursor = self.conn.cursor()

            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            self.cursor.execute("PRAGMA cache_size=10000")  # Larger cache

            print(f"Connected to database: {self.db_path}")
            print("WAL mode enabled for better concurrency")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

            print("Database connection closed.")

    def get_user_by_id(self, user_id: int) -> Optional[Tuple]:
        """Get user information by user ID."""
        try:
            query = """
            SELECT u.id, u.username, a.tag as alliance_tag
            FROM users u
            LEFT JOIN alliances a ON u.alliance_id = a.id
            WHERE u.id = ?
            """
            return self.execute_with_retry(query, (user_id,), "fetchone")
        except sqlite3.Error as e:
            print(f"Error fetching user by ID: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Tuple]:
        """Get user information by username."""
        try:
            query = """
            SELECT u.id, u.username, a.tag as alliance_tag
            FROM users u
            LEFT JOIN alliances a ON u.alliance_id = a.id
            WHERE u.username = ?
            """
            return self.execute_with_retry(query, (username,), "fetchone")
        except sqlite3.Error as e:
            print(f"Error fetching user by username: {e}")
            return None

    def list_user_reservations(self, user_id: int) -> List[Tuple]:
        """List all reservations for a user with formatted dates and minister details."""
        try:
            query = """
            SELECT r.id, r.schedule_date, r.schedule_time, r.created_at,
                   a.tag as alliance_tag, m.name as minister_name, 
                   GROUP_CONCAT(mt.name, ', ') as minister_types
            FROM reservations r
            LEFT JOIN alliances a ON r.alliance_id = a.id
            LEFT JOIN ministers m ON r.minister_id = m.id
            LEFT JOIN ministers_minister_types mmt ON m.id = mmt.ministers_id
            LEFT JOIN minister_types mt ON mmt.ministertype_id = mt.id
            WHERE r.user_id = ?
            GROUP BY r.id, r.schedule_date, r.schedule_time, r.created_at, a.tag, m.name
            ORDER BY r.schedule_date, r.schedule_time
            """
            result = self.execute_with_retry(query, (user_id,), "fetchall")
            return result if result else []
        except sqlite3.Error as e:
            print(f"Error fetching reservations: {e}")
            return []

    def get_reservation_details(self, reservation_id: int) -> Optional[Tuple]:
        """Get detailed information about a specific reservation including minister details."""
        try:
            query = """
            SELECT r.id, r.schedule_date, r.schedule_time, u.username, a.tag as alliance_tag,
                   m.name as minister_name, GROUP_CONCAT(mt.name, ', ') as minister_types
            FROM reservations r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN alliances a ON r.alliance_id = a.id
            LEFT JOIN ministers m ON r.minister_id = m.id
            LEFT JOIN ministers_minister_types mmt ON m.id = mmt.ministers_id
            LEFT JOIN minister_types mt ON mmt.ministertype_id = mt.id
            WHERE r.id = ?
            GROUP BY r.id, r.schedule_date, r.schedule_time, u.username, a.tag, m.name
            """
            return self.execute_with_retry(query, (reservation_id,), "fetchone")
        except sqlite3.Error as e:
            print(f"Error fetching reservation details: {e}")
            return None

    def get_total_reservations_count(self) -> int:
        """Get the total number of reservations in the database."""
        try:
            result = self.execute_with_retry("SELECT COUNT(*) FROM reservations", fetch_method="fetchone")
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"Error getting reservations count: {e}")
            return 0

    def get_reservations_summary(self) -> Optional[Tuple]:
        """Get a summary of reservations including total count and date range."""
        try:
            query = """
            SELECT COUNT(*) as total_count,
                   MIN(schedule_date) as earliest_date,
                   MAX(schedule_date) as latest_date,
                   COUNT(DISTINCT user_id) as unique_users
            FROM reservations
            """
            return self.execute_with_retry(query, fetch_method="fetchone")
        except sqlite3.Error as e:
            print(f"Error getting reservations summary: {e}")
            return None

    def display_reservation_details(self, reservation_id: int, username: str, alliance_tag: str,
                                    schedule_date: str, schedule_time: str, minister_name: str,
                                    minister_types: str):
        """Display reservation details in a consistent format."""
        formatted_datetime = self.format_datetime(schedule_date, schedule_time)

        print(f"\nReservation Details:")
        print(f"  ID: {reservation_id}")
        print(f"  User: {username}")
        if alliance_tag:
            print(f"  Alliance: {alliance_tag}")
        print(f"  Scheduled: {formatted_datetime}")
        if minister_name:
            minister_display = minister_name
            if minister_types:
                minister_display += f" ({minister_types})"
            print(f"  Minister: {minister_display}")

    def delete_reservation_by_id(self, reservation_id: int) -> bool:
        """Delete a specific reservation by ID."""
        try:
            check_result = self.execute_with_retry(
                "SELECT id FROM reservations WHERE id = ?",
                (reservation_id,),
                "fetchone"
            )

            if not check_result:
                print(f"Reservation with ID {reservation_id} not found.")
                return False

            self.execute_with_retry("DELETE FROM reservations WHERE id = ?", (reservation_id,))

            self.commit_with_retry()

            if self.cursor.rowcount > 0:
                print(f"Successfully deleted reservation with ID {reservation_id}")
                return True
            else:
                print(f"Failed to delete reservation with ID {reservation_id}")
                return False

        except sqlite3.Error as e:
            print(f"Error deleting reservation: {e}")
            self.rollback_with_retry()
            return False

    def delete_all_user_reservations(self, user_id: int) -> int:
        """Delete all reservations for a user. Returns count of deleted reservations."""
        try:
            # Get count before deletion
            count_result = self.execute_with_retry(
                "SELECT COUNT(*) FROM reservations WHERE user_id = ?",
                (user_id,),
                "fetchone"
            )
            count = count_result[0] if count_result else 0

            if count == 0:
                print(f"No reservations found for user ID {user_id}")
                return 0

            self.execute_with_retry("DELETE FROM reservations WHERE user_id = ?", (user_id,))

            self.commit_with_retry()

            deleted_count = self.cursor.rowcount
            print(f"Successfully deleted {deleted_count} reservation(s) for user ID {user_id}")
            return deleted_count

        except sqlite3.Error as e:
            print(f"Error deleting reservations: {e}")
            self.rollback_with_retry()
            return 0

    def delete_all_reservations(self) -> bool:
        """Delete all reservations from the table with confirmation."""
        try:
            # Get summary information before truncation
            summary = self.get_reservations_summary()
            if not summary:
                print("Error getting reservation summary.")
                return False

            total_count, earliest_date, latest_date, unique_users = summary

            if total_count == 0:
                print("No reservations found in the database.")
                return False

            print(f"\n{'=' * 60}")
            print("DELETE ALL RESERVATIONS - WARNING")
            print(f"{'=' * 60}")
            print(f"This operation will DELETE ALL reservations from the database!")
            print(f"\nCurrent database statistics:")
            print(f"  Total reservations: {total_count}")
            print(f"  Unique users with reservations: {unique_users}")
            if earliest_date and latest_date:
                print(f"  Date range: {earliest_date} to {latest_date}")
            print(f"\nDatabase file: {self.db_path}")
            print(f"{'=' * 60}")

            # First confirmation
            print("\n⚠️  WARNING: This action cannot be undone!")
            confirm1 = input("Are you sure you want to delete ALL reservations? (yes/no): ").strip().lower()

            if confirm1 != 'yes':
                print("Operation cancelled.")
                return False

            # Second confirmation with exact count
            print(f"\n⚠️  FINAL WARNING: You are about to delete {total_count} reservations.")
            confirm2 = input(f"Type 'DELETE {total_count} RESERVATIONS' to confirm: ").strip()

            expected_confirmation = f"DELETE {total_count} RESERVATIONS"
            if confirm2 != expected_confirmation:
                print("Operation cancelled - confirmation text did not match.")
                return False

            # Perform the deletion
            print("\nDeleting all reservations...")
            self.execute_with_retry("DELETE FROM reservations")

            # Reset the auto-increment counter
            self.execute_with_retry("DELETE FROM sqlite_sequence WHERE name='reservations'")

            self.commit_with_retry()

            deleted_count = self.cursor.rowcount
            print(f"\n✅ Successfully deleted {deleted_count} reservations.")
            print("The reservations table has been cleared.")
            print("Auto-increment counter has been reset.")

            return True

        except sqlite3.Error as e:
            print(f"Error deleting all reservations: {e}")
            self.rollback_with_retry()
            return False

    def delete_reservation_by_reservation_id(self, reservation_id: int) -> bool:
        """Delete a reservation by its ID directly with enhanced details."""
        try:
            reservation = self.get_reservation_details(reservation_id)

            if not reservation:
                print(f"Reservation with ID {reservation_id} not found.")
                return False

            res_id, schedule_date, schedule_time, username, alliance_tag, minister_name, minister_types = reservation

            self.display_reservation_details(res_id, username, alliance_tag, schedule_date,
                                             schedule_time, minister_name, minister_types)

            confirm = input(f"\nAre you sure you want to delete this reservation? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Deletion cancelled.")
                return False

            self.execute_with_retry("DELETE FROM reservations WHERE id = ?", (reservation_id,))

            self.commit_with_retry()

            if self.cursor.rowcount > 0:
                print(f"Successfully deleted reservation with ID {reservation_id}")
                return True
            else:
                print(f"Failed to delete reservation with ID {reservation_id}")
                return False

        except sqlite3.Error as e:
            print(f"Error deleting reservation: {e}")
            self.rollback_with_retry()
            return False

    def commit_with_retry(self, max_retries: int = None):
        """Commit transaction with retry logic."""
        if max_retries is None:
            max_retries = self.max_retries

        for attempt in range(max_retries):
            try:
                self.conn.commit()
                return
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "database is locked" in error_msg or "database is busy" in error_msg:
                    if attempt < max_retries - 1:
                        delay = random.uniform(*self.retry_delay_range)
                        print(f"Database is busy during commit, retrying in {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue
                raise

    def rollback_with_retry(self, max_retries: int = None):
        """Rollback transaction with retry logic."""
        if max_retries is None:
            max_retries = self.max_retries

        for attempt in range(max_retries):
            try:
                self.conn.rollback()
                return
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                if "database is locked" in error_msg or "database is busy" in error_msg:
                    if attempt < max_retries - 1:
                        delay = random.uniform(*self.retry_delay_range)
                        time.sleep(delay)
                        continue
                raise

    def format_datetime(self, date_str: str, time_str: str) -> str:
        """Format date and time for nice display."""
        try:
            datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")

            # Format as: "Monday, January 15, 2024 at 2:30 PM"
            return dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except ValueError:
            # If parsing fails, return original strings
            return f"{date_str} at {time_str}"

    def format_created_at(self, created_at_str: str) -> str:
        """Format created_at timestamp for display."""
        try:
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d"
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(created_at_str, fmt)
                    return dt.strftime("%A, %B %d, %Y at %I:%M %p")
                except ValueError:
                    continue

            return created_at_str
        except:
            return created_at_str

    def display_user_reservations(self, user_identifier: str):
        """Display all reservations for a user (by ID or username) with minister details."""
        try:
            user_id = int(user_identifier)
            user = self.get_user_by_id(user_id)
        except ValueError:
            user = self.get_user_by_username(user_identifier)
            if user:
                user_id = user[0]

        if not user:
            print(f"User '{user_identifier}' not found.")
            return

        user_id, username, alliance_tag = user
        print(f"\n{'=' * 60}")
        print(f"RESERVATIONS FOR USER: {username} (ID: {user_id})")
        if alliance_tag:
            print(f"Alliance: {alliance_tag}")
        print(f"{'=' * 60}")

        reservations = self.list_user_reservations(user_id)

        if not reservations:
            print("No reservations found for this user.")
            return

        print(f"\nFound {len(reservations)} reservation(s):\n")

        for i, (
                res_id, schedule_date, schedule_time, created_at, alliance_tag, minister_name,
                minister_types) in enumerate(
            reservations, 1):
            formatted_datetime = self.format_datetime(schedule_date, schedule_time)
            formatted_created = self.format_created_at(created_at)

            print(f"{i}. Reservation ID: {res_id}")
            print(f"   Scheduled: {formatted_datetime}")
            print(f"   Created: {formatted_created}")

            if alliance_tag:
                print(f"   Alliance: {alliance_tag}")

            if minister_name:
                minister_display = minister_name
                if minister_types:
                    minister_display += f" ({minister_types})"
                print(f"   Minister: {minister_display}")

            print()

    def interactive_delete(self, user_identifier: str):
        """Interactive deletion of reservations for a user with enhanced details."""
        # Get user information
        try:
            user_id = int(user_identifier)
            user = self.get_user_by_id(user_id)
        except ValueError:
            user = self.get_user_by_username(user_identifier)
            if user:
                user_id = user[0]

        if not user:
            print(f"User '{user_identifier}' not found.")
            return

        user_id, username, alliance_tag = user
        reservations = self.list_user_reservations(user_id)

        if not reservations:
            print(f"No reservations found for user {username}.")
            return

        print(f"\nFound {len(reservations)} reservation(s) for {username}:")

        while True:
            print("\nOptions:")
            print("1. Delete a specific reservation")
            print("2. Delete ALL reservations for this user")
            print("3. Cancel and return")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                print(f"\nReservations for {username}:")

                for i, (res_id, schedule_date, schedule_time, created_at, res_alliance_tag, minister_name,
                        minister_types) in enumerate(reservations, 1):
                    formatted_datetime = self.format_datetime(schedule_date, schedule_time)
                    display_text = f"{i}. ID {res_id}: {formatted_datetime}"
                    if minister_name:
                        display_text += f" - Minister: {minister_name}"
                        if minister_types:
                            display_text += f" ({minister_types})"

                    print(display_text)

                try:
                    selection = input(f"\nEnter reservation number to delete (1-{len(reservations)}): ").strip()
                    index = int(selection) - 1

                    if 0 <= index < len(reservations):
                        reservation_id = reservations[index][0]
                        schedule_date = reservations[index][1]
                        schedule_time = reservations[index][2]
                        res_alliance_tag = reservations[index][4]
                        minister_name = reservations[index][5]
                        minister_types = reservations[index][6]

                        self.display_reservation_details(reservation_id, username, res_alliance_tag,
                                                         schedule_date, schedule_time, minister_name, minister_types)

                        confirm = input(f"\nAre you sure you want to delete this reservation? (y/N): ").strip().lower()

                        if confirm == 'y':
                            if self.delete_reservation_by_id(reservation_id):
                                reservations = self.list_user_reservations(user_id)

                                if not reservations:
                                    print("No more reservations for this user.")
                                    break
                        else:
                            print("Deletion cancelled.")
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            elif choice == "2":
                print(f"\nAll reservations for {username}:")

                for i, (res_id, schedule_date, schedule_time, created_at, res_alliance_tag, minister_name,
                        minister_types) in enumerate(reservations, 1):
                    print(f"\n{i}.")

                    self.display_reservation_details(res_id, username, res_alliance_tag,
                                                     schedule_date, schedule_time, minister_name, minister_types)

                confirm = input(
                    f"\nAre you sure you want to delete ALL {len(reservations)} reservations for {username}? (y/N): ").strip().lower()

                if confirm == 'y':
                    deleted_count = self.delete_all_user_reservations(user_id)

                    if deleted_count > 0:
                        break
                else:
                    print("Deletion cancelled.")

            elif choice == "3":
                print("Operation cancelled.")
                break

            else:
                print("Invalid choice. Please select 1, 2, or 3.")


def main():
    """Main function to run the reservation manager."""
    parser = argparse.ArgumentParser(description="Reservation Management System")
    parser.add_argument(
        "--db",
        "--database",
        dest="db_path",
        default="database/production.db",
        help="Path to the SQLite database file (default: database/production.db)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.db_path):
        print(f"Error: Database file '{args.db_path}' not found.")
        print("Please check the path and try again.")
        sys.exit(1)

    manager = ReservationManager(args.db_path)

    try:
        manager.connect()

        while True:
            print("\n" + "=" * 50)
            print("RESERVATION MANAGEMENT SYSTEM")
            print("=" * 50)
            print("1. List user reservations")
            print("2. Delete user reservations")
            print("3. Delete reservation by ID")
            print("4. Delete ALL reservations (⚠️  DANGER)")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                user_identifier = input("Enter user ID or username: ").strip()
                if user_identifier:
                    manager.display_user_reservations(user_identifier)
                else:
                    print("Please enter a valid user ID or username.")

            elif choice == "2":
                user_identifier = input("Enter user ID or username: ").strip()
                if user_identifier:
                    manager.interactive_delete(user_identifier)
                else:
                    print("Please enter a valid user ID or username.")

            elif choice == "3":
                reservation_id = input("Enter reservation ID to delete: ").strip()
                if reservation_id:
                    try:
                        res_id = int(reservation_id)
                        manager.delete_reservation_by_reservation_id(res_id)
                    except ValueError:
                        print("Please enter a valid numeric reservation ID.")
                else:
                    print("Please enter a valid reservation ID.")

            elif choice == "4":
                manager.delete_all_reservations()

            elif choice == "5":
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please select 1, 2, 3, 4, or 5.")
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user.")
    finally:
        manager.close()


if __name__ == "__main__":
    main()