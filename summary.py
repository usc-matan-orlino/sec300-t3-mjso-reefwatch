"""Daily summary: aggregate one day's surveys in Cosmos DB, store the result in Azure SQL.

Run from the command line (for example from a scheduler at the end of the day):
    python summary.py             # summary for today
    python summary.py 2026-10-15  # summary for a given date
"""

import os
import sys
from datetime import date

import pymssql
from apscheduler.schedulers.background import BackgroundScheduler

from db import get_collection, get_sql_connection


def generate_summary(summary_date):
    """Create the summary for one date (YYYY-MM-DD).

    Returns (True, message) when saved, or (False, message) when it was
    not saved, for example because the date already has a summary.
    """
    conn = get_sql_connection()
    try:
        cursor = conn.cursor()

        # Prevent duplicates (the primary key on summary_date also enforces this).
        cursor.execute("SELECT 1 FROM daily_summary WHERE summary_date = %s", (summary_date,))
        if cursor.fetchone():
            return False, f"A summary for {summary_date} already exists."

        # Total surveys and total cost.
        totals = list(get_collection("surveys").aggregate([
            {"$match": {"survey_date": summary_date}},
            {"$group": {"_id": None, "total_surveys": {"$sum": 1},
                        "total_cost": {"$sum": "$survey_cost"}}},
        ]))
        total_surveys = totals[0]["total_surveys"] if totals else 0
        total_cost = totals[0]["total_cost"] if totals else 0

        # Most frequently observed species.
        species = list(get_collection("surveys").aggregate([
            {"$match": {"survey_date": summary_date}},
            {"$unwind": "$species_observed"},
            {"$group": {"_id": "$species_observed", "total": {"$sum": 1}}},
            {"$sort": {"total": -1}},
            {"$limit": 1},
        ]))
        top_species = species[0]["_id"] if species else None

        # Equipment at or below its low stock limit.
        low_equipment = list(get_collection("equipment").aggregate([
            {"$project": {"name": 1,
                          "low": {"$lte": ["$available_quantity", "$low_stock_threshold"]}}},
            {"$match": {"low": True}},
        ]))
        alerts = ", ".join(item["name"] for item in low_equipment)[:500] or None

        try:
            cursor.execute(
                "INSERT INTO daily_summary "
                "(summary_date, total_surveys, total_survey_cost, top_species, low_equipment_alerts) "
                "VALUES (%s, %s, %s, %s, %s)",
                (summary_date, total_surveys, total_cost, top_species, alerts),
            )
            conn.commit()
        except pymssql.IntegrityError:
            return False, f"A summary for {summary_date} already exists."

        return True, f"Summary for {summary_date} saved."
    finally:
        conn.close()


def get_summaries():
    """Return all stored summaries as dictionaries, newest first."""
    conn = get_sql_connection()
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(
            "SELECT summary_date, total_surveys, total_survey_cost, top_species, "
            "low_equipment_alerts FROM daily_summary ORDER BY summary_date DESC"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def run_daily_summary():
    """Scheduled job: generate today's summary."""
    print(generate_summary(date.today().isoformat())[1])


def start_scheduler():
    """Run the daily summary every day at SUMMARY_TIME (HH:MM, 24 hour, set in .env)."""
    hour, minute = os.getenv("SUMMARY_TIME", "17:00").split(":")
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_summary, "cron", hour=int(hour), minute=int(minute))
    scheduler.start()
    print(f"Daily summary scheduled for {int(hour):02d}:{int(minute):02d}")


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    print(generate_summary(target_date)[1])
