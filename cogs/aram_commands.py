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
import random
from datetime import datetime


load_dotenv()


logger = logging.getLogger("araminator")


class ARAMCommands(commands.Cog, name="ARAM commands"):
    def __init__(self, bot):
        self.bot = bot
        self.session_active = False
        self.session_message = None

    @discord.slash_command(description="Start a custom game ARAM session.")
    async def aram(self, ctx: discord.ApplicationContext):

        if self.session_active:
            await ctx.respond("An ARAM session is already active!", ephemeral=True)
            return

        self.session_active = True

        embed = discord.Embed(
            title="🏆 ARAM Session",
            description="Click the button below to join!",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Signed-up Players", value="No one has signed up yet!", inline=False
        )

        await ctx.send(embed=embed, view=ARAMView(self.bot, None))

    @discord.slash_command(description="End a custom game ARAM session.")
    async def end_aram(self, ctx: discord.ApplicationContext):
        pass


class ARAMView(discord.ui.View):
    def __init__(self, bot, message):
        super().__init__(timeout=None)
        self.champions = {}
        self.message = message
        self.bot = bot
        self.team_1 = {}
        self.team_2 = {}
        self.team_1_champions = {}
        self.team_2_champions = {}
        self.champions = {}

    @discord.ui.button(label="Join!", style=discord.ButtonStyle.green, emoji="😎")
    async def join_aram(self, button, interaction: discord.Interaction):
        db_connection = get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        cursor.execute(
            """SELECT * FROM player WHERE discord_id = %s
            """,
            (interaction.user.id,),
        )
        player = cursor.fetchone()

        if not player:
            await interaction.response.send_message(
                "❌ You need to register first using `/register`.",
                ephemeral=True,
                delete_after=10,
            )
            return

        if str(player["discord_id"]) in self.champions.keys():
            await interaction.response.send_message(
                "❌ You already in the current ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            return

        self.champions[player["discord_id"]] = {
            "riot_game_name": player["riot_game_name"],
            "riot_game_tagline": player["riot_game_tagline"],
            "riot_puuid": player["riot_puuid"],
        }

        await self.update_message()

        await interaction.response.send_message(
            f"✅ **{interaction.user.mention}** joined the ARAM session!",
            ephemeral=True,
            delete_after=3,
        )

    @discord.ui.button(label="Leave!", style=discord.ButtonStyle.red, emoji="😎")
    async def leave_aram(self, button, interaction: discord.Interaction):
        discord_id = interaction.user.id

        if str(discord_id) not in self.champions.keys():
            await interaction.response.send_message(
                "❌ You are not in the current ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            return

        if self.champions.pop(str(discord_id), None):
            await interaction.response.send_message(
                f"🚪 **{interaction.user.mention}** left the ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            await self.update_message()

    @discord.ui.button(
        label="Roll Teams!", style=discord.ButtonStyle.blurple, emoji="🎲"
    )
    async def roll_teams(self, button, interaction: discord.Interaction):
        # if len(self.champions) < 2:
        #     await interaction.response.send_message(
        #         "❌ Not enough players to form teams!", ephemeral=True, delete_after=5
        #     )
        #     return
        await interaction.response.defer()
        user_keys = list(self.champions.keys())

        random.shuffle(user_keys)

        mid = len(user_keys) // 2
        team_1_keys = user_keys[:mid]
        team_2_keys = user_keys[mid:]

        # Reconstruct dictionaries for the teams
        self.team_1 = {key: self.champions[key] for key in team_1_keys}
        self.team_2 = {key: self.champions[key] for key in team_2_keys}

        await self.update_message()

    @discord.ui.button(
        label="Roll Champions!", style=discord.ButtonStyle.blurple, emoji="🎲"
    )
    async def roll_champions(self, button, interaction: discord.Interaction):
        if not (self.team_1 or self.team_2):
            await interaction.response.send_message(
                "❌ Atleast one team needs to have players!",
                ephemeral=True,
                delete_after=5,
            )
            return
        await interaction.response.defer()

        if not self.champions:
            self.champions = self.update_champions()

        team_size = max(len(self.team_1), len(self.team_2))

        total_champions_needed = team_size * 4

        champion_pool = self.get_random_champions(total_champions_needed)
        random.shuffle(champion_pool)

        mid = len(champion_pool) // 2
        self.team_1_champions = champion_pool[:mid]
        self.team_2_champions = champion_pool[mid:]

        # # Reconstruct dictionaries for the teams
        # self.team_1_champions = {key: self.champions[key] for key in team_1_champions}
        # self.team_2_champions = {key: self.champions[key] for key in team_2_champions}
        await self.update_message()

    def get_random_champions(self, pool_size):
        """Fetch random champions from the database."""
        db_connection = get_db_connection()
        cursor = db_connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Champion ORDER BY RAND() LIMIT %s", (pool_size,))
        champions = cursor.fetchall()

        cursor.close()
        db_connection.close()
        return champions

    async def update_message(self):
        """Updates the message with the current player list"""
        signed_up_mentions = [
            f"<@{discord_id}> ({player_data["riot_game_name"]})"
            for discord_id, player_data in self.champions.items()
        ]

        team_1_mentions = [
            f"<@{discord_id}> ({player_data["riot_game_name"]})"
            for discord_id, player_data in self.team_1.items()
        ]
        team_1_champions = [
            f"<:{champion_data["id"]}:{champion_data["emoji_id"]}>{champion_data['name']}"
            for champion_data in self.team_1_champions
        ]
        team_2_champions = [
            f"<:{champion_data["id"]}:{champion_data["emoji_id"]}>{champion_data['name']}"
            for champion_data in self.team_2_champions
        ]
        team_2_mentions = [
            f"<@{discord_id}> ({player_data["riot_game_name"]})"
            for discord_id, player_data in self.team_2.items()
        ]

        embed = discord.Embed(
            title="🏆 ARAM Session",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )
        embed.add_field(
            name="# Signed-up Players",
            value=(
                "\n".join(signed_up_mentions)
                if signed_up_mentions
                else "No one has signed up yet!"
            ),
            inline=False,
        )

        if self.team_1:
            embed.add_field(
                name="Team 1 Players",
                value=("\n".join(team_1_mentions)),
                inline=True,
            )
            embed.add_field(
                name="Team 1 champions",
                value=(
                    "\n".join(team_1_champions)
                    if team_1_champions
                    else "No champions assigned to team 1!"
                ),
                inline=True,
            )
        embed.add_field(name="\u200B", value="\u200B", inline=False)

        if self.team_2:
            embed.add_field(
                name="Team 2 Players",
                value=("\n".join(team_2_mentions)),
                inline=True,
            )
            embed.add_field(
                name="Team 2 champions",
                value=(
                    "\n".join(team_2_champions)
                    if team_2_champions
                    else "No champions assigned to team 2!"
                ),
                inline=True,
            )

        await self.message.edit(embed=embed, view=self)


def setup(bot):
    bot.add_cog(ARAMCommands(bot))
