
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load the .env file from the backend folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection_string():
    required_settings = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]

    missing = [
        setting for setting in required_settings
        if not os.getenv(setting)
    ]

    if missing:
        raise RuntimeError(
            "Missing database settings: " + ", ".join(missing)
        )

    return (
        f"host={os.getenv('DB_HOST')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')}"
    )


# Return a real PostgreSQL connection, not a context manager generator
def get_connection():
    return psycopg.connect(
        get_connection_string(),
        row_factory=dict_row
    )


def check_database():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    current_database() AS database_name,
                    PostGIS_Full_Version() AS postgis_version,
                    to_regclass('public.tourist_attractions') IS NOT NULL
                        AS table_exists;
            """)

            result = cursor.fetchone()

        return {
            "database_connected": bool(result["table_exists"]),
            "database_name": result["database_name"],
            "postgis_version": result["postgis_version"],
            "table_exists": result["table_exists"]
        }

    except Exception as error:
        return {
            "database_connected": False,
            "error": str(error)
        }

    finally:
        if connection is not None:
            connection.close()
