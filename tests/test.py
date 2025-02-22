# import sqlite3
# conn = sqlite3.connect('araminator.db')

# cur = conn.cursor()

# cur.execute('CREATE TABLE IF NOT EXISTS guild(id INTEGER PRIMARY KEY)')


# res = cur.execute("SELECT * FROM guild")
import os
from dotenv import load_dotenv
import mysql.connector
load_dotenv()


DB_HOST=os.environ.get("DB_HOST")
DB_ROOT_USERNAME=os.getenv("DB_ROOT_USERNAME")
DB_ROOT_PASSWORD=os.getenv("DB_ROOT_PASSWORD")

def db_connect():
    try:
        db = mysql.connector.connect(
            host=DB_HOST,
            user=DB_ROOT_USERNAME, 
            password=DB_ROOT_PASSWORD,
        )
        with db.cursor() as cursor: 
            cursor.execute("CREATE DATABASE IF NOT EXISTS Araminator")
    except mysql.connector.Error as e: 
        print(e)


if __name__ == "__main__": 
    db_connect()