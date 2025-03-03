import os
import sys
from urllib3.exceptions import NameResolutionError
from requests.exceptions import ConnectionError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.database import get_db_connection
from utils.riot_api import (
    fetch_free_champion_rotation,
    fetch_champion_data,
    fetch_condensed_champion_data,
    fetch_champion_tile_images,
)


def display_champions():
    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute(f"SELECT * FROM champion")
    champions = cursor.fetchall()

    return champions


if __name__ == "__main__":
    print(display_champions())
