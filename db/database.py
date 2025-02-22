import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_ROOT_USERNAME = os.getenv("DB_ROOT_USERNAME")
DB_ROOT_PASSWORD = os.getenv("DB_ROOT_PASSWORD")
DB_TABLE = os.getenv("DB_TABLE")


def create_database():
    """Connect to MySQL server and create databse if missing."""
    db_connection = mysql.connector.connect(
        host=DB_HOST, user=DB_ROOT_USERNAME, password=DB_ROOT_PASSWORD
    )

    # Create database if it doesn't exist
    with db_connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_TABLE}")

    db_connection.commit()
    db_connection.close()


def get_db_connection():
    """Connect to MySQL and return a Connection Object"""
    create_database()  # Ensure databse exists
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_ROOT_USERNAME,
        password=DB_ROOT_PASSWORD,
        database=DB_TABLE,
    )


def init_db():
    """Initialize database by creating tables if they do not exist"""
    db_connection = get_db_connection()

    with db_connection.cursor() as cursor:
        # Players table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS player (
            discord_id VARCHAR(50) PRIMARY KEY,
            riot_game_name VARCHAR(50) UNIQUE NOT NULL,
            riot_game_tagline VARCHAR(50) UNIQUE NOT NULL,
            riot_puuid VARCHAR(100) UNIQUE NOT NULL
        )
        """
        )

    db_connection.commit()
    db_connection.close()
