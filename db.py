"""Database connections for ReefWatch (Cosmos DB for MongoDB and Azure SQL)."""

import os

import pymssql
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # read settings from the .env file


def get_collection(name):
    """Return a Mongo collection: 'surveys', 'equipment' or 'partners'."""
    client = MongoClient(os.getenv("COSMOS_CONNECTION_STRING"))
    return client[os.getenv("COSMOS_DATABASE")][name]


def get_sql_connection():
    """Return a new Azure SQL connection. Close it when finished."""
    return pymssql.connect(
        server=os.getenv("SQL_SERVER"),
        user=os.getenv("SQL_USER"),
        password=os.getenv("SQL_PASSWORD"),
        database=os.getenv("SQL_DATABASE"),
    )


if __name__ == "__main__":
    # Quick check that both connections work.
    for name in ("surveys", "equipment", "partners"):
        print(f"Cosmos collection '{name}': {get_collection(name).count_documents({})} documents")

    conn = get_sql_connection()
    conn.close()
    print("Azure SQL OK")
