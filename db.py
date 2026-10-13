"""Database connections for ReefWatch (Cosmos DB and Azure SQL)."""

import os

import pymssql
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()  # read settings from the .env file


def get_cosmos_database():
    """Return the Cosmos DB database object."""
    client = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
    return client.get_database_client(os.getenv("COSMOS_DATABASE"))


def get_container(name):
    """Return a Cosmos container: 'surveys', 'equipment' or 'partners'."""
    return get_cosmos_database().get_container_client(name)


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
    for container_name in ("surveys", "equipment", "partners"):
        get_container(container_name).read()
        print(f"Cosmos container '{container_name}' OK")

    conn = get_sql_connection()
    conn.close()
    print("Azure SQL OK")
