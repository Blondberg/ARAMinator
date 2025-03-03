import logging
import discord
from discord.ext import commands
from discord import option
import os
from dotenv import load_dotenv
from db.database import get_db_connection
from utils.riot_api import (
    get_puuid_from_riot_id,
    fetch_champion_tile_images,
    fetch_condensed_champion_data,
)
from utils.exceptions import InvalidRiotIDFormatError


load_dotenv()


logger = logging.getLogger("araminator")


class PlayerCommands(commands.Cog, name="Player commands"):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        description="Registers user and links Riot ID with Discord ID"
    )
    @option("riot_id", description="SummonerName#Tag")
    @option(
        "region",
        description="Region to which you account belongs to",
        choices=["europe", "americas", "asia", "esports"],
        default="europe",
    )
    async def register(
        self, ctx: discord.ApplicationContext, riot_id: str, region: str
    ):
        try:
            account_details = get_puuid_from_riot_id(riot_id, region)
        except InvalidRiotIDFormatError as e:
            await ctx.respond(str(e), ephemeral=True)
            return

        if not account_details:
            await ctx.respond(
                f"Riot ID {riot_id} could not be found. Please check name and region.",
                ephemeral=True,
            )
            return

        riot_game_name = account_details["gameName"]
        riot_tag_line = account_details["tagLine"]
        riot_puuid = account_details["puuid"]

        db_connection = get_db_connection()
        cursor = db_connection.cursor()

        discord_id = str(ctx.author.id)
        cursor.execute(f"SELECT * FROM player WHERE discord_id = {discord_id}")
        existing_player = cursor.fetchone()

        if existing_player:
            cursor.execute(
                """
                UPDATE player 
                SET riot_game_name = %s, riot_game_tagline = %s, riot_puuid = %s
                WHERE discord_id = %s
                """,
                (discord_id, riot_game_name, riot_tag_line, riot_puuid),
            )
            await ctx.respond(
                f"You were already registered, but I updated your information! {ctx.author.mention} registered as **{riot_game_name}#{riot_tag_line}**",
                ephemeral=True,
            )
        else:
            cursor.execute(
                "INSERT INTO player (discord_id, riot_game_name, riot_game_tagline, riot_puuid) VALUES (%s, %s, %s, %s)",
                (discord_id, riot_game_name, riot_tag_line, riot_puuid),
            )
            db_connection.commit()
            await ctx.respond(
                f"✅ {ctx.author.mention} registered as **{riot_game_name}#{riot_tag_line}**!",
                ephemeral=True,
            )

        cursor.close()
        db_connection.close()

    @discord.slash_command(
        description="Making sure champion data and images are synced and up-to-date."
    )
    @commands.is_owner()
    async def sync_champion_data(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        # Download champion square/tile images
        fetch_champion_tile_images()

        db_connection = get_db_connection()
        cursor = db_connection.cursor()

        # Create table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Champion(
                `key` INT PRIMARY KEY,
                id VARCHAR(50) UNIQUE NOT NULL, 
                name VARCHAR(50) UNIQUE NOT NULL,
                sprite VARCHAR(60),
                emoji_id UNSIGNED BIGINT UNQIUE
            )
            """
        )

        champions = fetch_condensed_champion_data()

        for champ in champions:
            # Insert champions (update entry if existing)
            cursor.execute(
                """
                INSERT INTO Champion (`key`, id, name, sprite)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id = VALUES(id),
                    name = VALUES(name),
                    sprite = VALUES(sprite)
                """,
                (champ["key"], champ["id"], champ["name"], champ["sprite"]),
            )

        db_connection.commit()
        cursor.close()
        db_connection.close()

        await ctx.respond("Champion data synced.", ephemeral=True)

    @discord.slash_command(description="Display all champion names with their icons")
    @commands.is_owner()
    async def display_champions(self, ctx: discord.ApplicationContext):
        db_connection = get_db_connection()
        cursor = db_connection.cursor()

        cursor.execute(f"SELECT * FROM champion")
        champions = cursor.fetchall()

        msg_string = ""

        for champ in champions:
            msg_string += f"{champ[2]}<:{champ[1]}:{champ[4]}>\n"

        await ctx.respond(msg_string[:1998])


def setup(bot):
    bot.add_cog(PlayerCommands(bot))
