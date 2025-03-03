import os
import requests
from dotenv import load_dotenv
from .exceptions import InvalidRiotIDFormatError
from enum import Enum
from typing import Literal
from urllib3.exceptions import NameResolutionError
from requests.exceptions import ConnectionError

load_dotenv()

RIOT_API_KEY = os.getenv("RIOT_API_KEY")

type RegionAbbreviations = Literal["EUW1", "NA1"]


def get_puuid_from_riot_id(
    riot_id: str,
    region="europe",
):
    """Fetch account PUUID from Riot API

    Args:
        riot_id (str): Riot ID (Game name and Tagline)
        region (str, optional): Riot region (americas, europe, asia, esports). Defaults to "europe".

    Returns:
        dict: Dictionary containing Riot ID (Game name and Tag line) and PUUID, or None if nothing is found
    """
    # Split summoner name and tag
    try:
        game_name, tag_line = riot_id.split("#")
    except ValueError:
        raise InvalidRiotIDFormatError(
            f"**{riot_id}** has an invalid Riot ID format. Make sure the Summoner Name and Tag are separated by #."
        )

    url = f"https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line.upper()}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return {
            "puuid": data["puuid"],
            "gameName": data["gameName"],
            "tagLine": data["tagLine"],
        }
    elif response.status_code == 404:
        return None  # Summoner not found
    else:
        raise Exception(f"Error {response.status_code}, {url}: {response.text}")


def fetch_champion_data():
    patches = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    latest_patch = patches.json()[0]

    url = f"https://ddragon.leagueoflegends.com/cdn/{latest_patch}/data/en_US/champion.json"
    try:
        response = requests.get(url)
    except (NameResolutionError, ConnectionError):
        raise

    if response.status_code == 200:
        data = response.json()
        return data["data"]
    elif response.status_code == 404:
        return None
    else:
        raise Exception(f"Error {response.status_code}, {url}: {response.text}")


def fetch_free_champion_rotation(region):
    url = f"https://{region}.api.riotgames.com/lol/platform/v3/champion-rotations"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    try:
        response = requests.get(url, headers=headers)
    except (NameResolutionError, ConnectionError):
        raise

    if response.status_code == 200:
        data = response.json()
        return data
    elif response.status_code == 404:
        return None
    else:
        raise Exception(f"Error {response.status_code}, {url}: {response.text}")


def fetch_condensed_champion_data():
    """Fetches all champion data, but condenses it down to id, name, key and sprite"""
    champion_data = fetch_champion_data()

    condensed_data = [
        {
            "id": d["id"],
            "name": d["name"],
            "key": d["key"],
            "sprite": f"{d["id"]}.png",
        }
        for d in champion_data.values()
    ]

    return condensed_data


def fetch_champion_tile_images():
    patches = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    latest_patch = patches.json()[0]

    champions = fetch_champion_data()

    square_image_base_url = (
        f"https://ddragon.leagueoflegends.com/cdn/{latest_patch}/img/champion/"
    )

    save_path = "assets/images/champion_squares/"
    os.makedirs(save_path, exist_ok=True)

    try:
        champions = fetch_champion_data()

        for champ_data in champions.values():
            champ_name = champ_data["id"]
            img_response = requests.get(f"{square_image_base_url}{champ_name}.png")

            if img_response.status_code == 200:
                img_path = os.path.join(save_path, f"{champ_name}.png")
                with open(img_path, "wb") as img_file:
                    img_file.write(img_response.content)
                print(f"Downloaded {champ_name}.png")
            else:
                print(f"Failed to download {champ_name}.png")
    except (NameResolutionError, ConnectionError) as e:
        raise
