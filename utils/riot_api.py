import os
import requests
from dotenv import load_dotenv

load_dotenv()
RIOT_API_KEY = os.getenv("RIOT_API_KEY")


def get_puuid_from_riot_id(
    riot_id: str,
    region="europe",
):
    """Fetch account PUUID from Riot API

    Args:
        riot_id (str): Riot ID (Game name and Tagline)
        region (str, optional): Riot region (Americas, europe, Asia, esports). Defaults to "europe".

    Returns:
        dict: Dictionary containing Riot ID (Game name and Tag line) and PUUID, or None if nothing is found
    """
    # Split summoner name and tag
    game_name, tag_line = riot_id.split("#")

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


if __name__ == "__main__":
    print(get_puuid_from_riot_id("leblond#euw"))
