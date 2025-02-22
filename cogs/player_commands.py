import logging
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.database import get_db_connection
from utils.riot_api import get_puuid_from_riot_id

load_dotenv()


logger = logging.getLogger("araminator")


class PlayerCommands(commands.Cog, name="Player commands"):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(
        description="Registers user and links Summoner name and ID with Discord ID"
    )
    async def register(
        self, ctx: discord.ApplicationContext, riot_id: str, region: str = "europe"
    ):
        account_details = get_puuid_from_riot_id(riot_id, region)

        if not account_details:
            await ctx.respond(
                f"Riot ID {riot_id} could not be found. Please check name and region."
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
                f"You were already registered, but I updated your information! {ctx.author.mention} registered as **{riot_game_name}#{riot_tag_line}**"
            )
        else:
            cursor.execute(
                "INSERT INTO player (discord_id, riot_game_name, riot_game_tagline, riot_puuid) VALUES (%s, %s, %s, %s)",
                (discord_id, riot_game_name, riot_tag_line, riot_puuid),
            )
            db_connection.commit()
            await ctx.respond(
                f"✅ {ctx.author.mention} registered as **{riot_game_name}#{riot_tag_line}**!"
            )

        cursor.close()
        db_connection.close()


def setup(bot):
    bot.add_cog(PlayerCommands(bot))
