import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

DB_HOST=os.environ.get("DB_HOST")
DB_ROOT_USERNAME=os.getenv("DB_ROOT_USERNAME")
DB_ROOT_PASSWORD=os.getenv("DB_ROOT_PASSWORD")
DB_TABLE=os.getenv("DB_TABLE")


def create_database(): 
    """Connect to MySQL server and create databse if missing.
    """
    db = mysql.connector.connect(
        host=DB_HOST,
        user=DB_ROOT_USERNAME,
        password=DB_ROOT_PASSWORD
    )
    
    # Create database if it doesn't exist
    with db.cursor() as cursor: 
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_TABLE}")
        
    db.commit()
    db.close()
        
    

def get_db_connection(): 
    """Connect to MySQL and return a Connection Object
    """
    create_database() # Ensure databse exists
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_ROOT_USERNAME,
        password=DB_ROOT_PASSWORD
    )

def init_db(): 
    """Initialize database by creating tables if they do not exist
    """
    db = get_db_connection() 
    cursor = db.cursor()
    
    with db.cursor() as cursor: 
        # Players table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS player (
            player_id INT AUTO_INCREMENT PRIMARY KEY,
            discord_id VARCHAR(50) UNIQUE NOT NULL,
            league_id VARCHAR(50) UNIQUE NOT NULL
            league_username VARCHAR(50) UNIQUE NOT NULL
        )
        """)

    db.commit() 
    db.close() 