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
import functools


load_dotenv()


logger = logging.getLogger("araminator")


def requires_session(func):
    """Decorator to ensure the user is in the ARAM session before allowing interaction."""

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        # Detect interaction argument dynamically (it will always be the last one)
        interaction = args[-1]  # Interaction is always the last positional argument

        if not isinstance(interaction, discord.Interaction):
            raise TypeError("Expected discord.Interaction as the last argument.")

        user_id = str(interaction.user.id)

        if user_id not in self.signed_up_users:
            await interaction.response.send_message(
                "❌ You are not in the current ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            return

        return await func(self, *args, **kwargs)

    return wrapper


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
            timestamp=datetime.now(),
        )
        embed.add_field(
            name="Signed-up Players", value="No one has signed up yet!", inline=False
        )

        message = await ctx.respond(embed=embed, view=ARAMView(self.bot, None))

        self.session_message = await message.original_response()

    @discord.slash_command(description="End a custom game ARAM session.")
    async def end_aram(self, ctx: discord.ApplicationContext):
        if not self.session_active:
            await ctx.respond("❌ No active ARAM session to end!", ephemeral=True)
            return

        self.session_active = False

        if self.session_message:
            try:
                await self.session_message.delete()
            except discord.NotFound:
                pass

        self.session_message = None

        await ctx.respond(
            "🛑 The ARAM session has been **ended**.", ephemeral=False, delete_after=10
        )


class ARAMView(discord.ui.View):
    def __init__(self, bot, message):
        super().__init__(timeout=None)
        self.signed_up_users = {}
        self.message = message
        self.bot = bot
        self.team_1 = {}
        self.team_2 = {}
        self.team_1_champions = {}
        self.team_2_champions = {}

    @discord.ui.button(label="Join!", style=discord.ButtonStyle.green, row=0)
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

        # Check if player is already in session
        if str(player["discord_id"]) in self.signed_up_users.keys():
            await interaction.response.send_message(
                "❌ You already in the current ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            return

        self.signed_up_users[player["discord_id"]] = {
            "riot_game_name": player["riot_game_name"],
            "riot_game_tagline": player["riot_game_tagline"],
            "riot_puuid": player["riot_puuid"],
        }

        await self.update_message()

        await interaction.response.send_message(
            f"✅ You joined the ARAM session!",
            ephemeral=True,
            delete_after=3,
        )

    @requires_session
    @discord.ui.button(label="Leave!", style=discord.ButtonStyle.red, row=0)
    async def leave_aram(self, button, interaction: discord.Interaction):
        discord_id = interaction.user.id

        if self.signed_up_users.pop(str(discord_id), None):
            self.team_1.pop(str(discord_id), None)
            self.team_2.pop(str(discord_id), None)

            await interaction.response.send_message(
                f"🚪 You left the ARAM session.",
                ephemeral=True,
                delete_after=3,
            )
            await self.update_message()

    @requires_session
    @discord.ui.button(
        label="Roll Teams!", style=discord.ButtonStyle.blurple, emoji="🎲", row=1
    )
    async def roll_teams(self, button, interaction: discord.Interaction):
        # if len(self.signed_up_users) < 2:
        #     await interaction.response.send_message(
        #         "❌ Not enough players to form teams!", ephemeral=True, delete_after=5
        #     )
        #     return
        await interaction.response.defer()
        user_keys = list(self.signed_up_users.keys())

        random.shuffle(user_keys)

        mid = len(user_keys) // 2
        if len(user_keys) % 2 == 1:
            if random.choice([True, False]):
                mid += 1  # Team 1 gets the extra player
        team_1_keys = user_keys[:mid]
        team_2_keys = user_keys[mid:]

        # Reconstruct dictionaries for the teams
        self.team_1 = {key: self.signed_up_users[key] for key in team_1_keys}
        self.team_2 = {key: self.signed_up_users[key] for key in team_2_keys}

        await self.update_message()

    @requires_session
    @discord.ui.button(
        label="Roll Champions!", style=discord.ButtonStyle.blurple, emoji="🎲", row=2
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

        self.assign_champions()

        await self.update_message()

    def assign_champions(self):
        """Assigns champions to both teams"""

        team_size = max(len(self.team_1), len(self.team_2))
        total_champions_needed = team_size * 4
        champion_pool = self.get_random_champions(total_champions_needed)

        random.shuffle(champion_pool)

        mid = len(champion_pool) // 2
        self.team_1_champions = champion_pool[:mid]
        self.team_2_champions = champion_pool[mid:]

    @requires_session
    @discord.ui.button(
        label="Swap team",
        style=discord.ButtonStyle.gray,
        emoji="↔️",
        row=1,
    )
    async def swap_team(
        self, select: discord.ui.Select, interaction: discord.Interaction
    ):
        discord_id = str(interaction.user.id)

        if discord_id in self.team_1:
            self.team_1.pop(discord_id)  # Remove from Team 1
            self.team_2[discord_id] = self.signed_up_users[discord_id]  # Move to Team 2
            new_team = "Team 2"
        else:
            self.team_2.pop(discord_id, None)  # Remove from Team 2
            self.team_1[discord_id] = self.signed_up_users[discord_id]  # Move to Team 1
            new_team = "Team 1"

        await self.update_message()

        await interaction.response.send_message(
            f"✅ You have switched to **{new_team}**!", ephemeral=True, delete_after=3
        )

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
        embeds = []
        """Updates the message with the current player list"""
        signed_up_mentions = [
            f"<@{discord_id}> ({data["riot_game_name"]})"
            for discord_id, data in self.signed_up_users.items()
        ]

        team_1_mentions = [
            f"<@{discord_id}> ({data["riot_game_name"]})"
            for discord_id, data in self.team_1.items()
        ]
        team_2_mentions = [
            f"<@{discord_id}> ({player_data["riot_game_name"]})"
            for discord_id, player_data in self.team_2.items()
        ]

        team_1_champions = [
            f"<:{champ["id"]}:{champ["emoji_id"]}>{champ['name']}"
            for champ in self.team_1_champions
        ]
        team_2_champions = [
            f"<:{champ["id"]}:{champ["emoji_id"]}>{champ['name']}"
            for champ in self.team_2_champions
        ]

        embed = discord.Embed(
            title="🏆 ARAM Session",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )
        embed.add_field(
            name="Signed-up Players",
            value=(
                "\n".join(signed_up_mentions)
                if signed_up_mentions
                else "No one has signed up yet!"
            ),
            inline=False,
        )
        embeds.append(embed)

        if self.team_1:
            embed = discord.Embed(
                title="Team 1",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Players",
                value=("\n".join(team_1_mentions)),
                inline=True,
            )
            embed.add_field(
                name="Champion Pool",
                value=(
                    "\n".join(team_1_champions)
                    if team_1_champions
                    else "No champions assigned."
                ),
                inline=True,
            )
            embeds.append(embed)
        # embed.add_field(name="\u200B", value="\u200B", inline=False)  # Spacer

        if self.team_2:
            embed = discord.Embed(
                title="Team 2",
                color=discord.Color.blue(),
            )
            embed.add_field(
                name="Players",
                value=("\n".join(team_2_mentions)),
                inline=True,
            )
            embed.add_field(
                name="Champion Pool",
                value=(
                    "\n".join(team_2_champions)
                    if team_2_champions
                    else "No champions assigned."
                ),
                inline=True,
            )
            embeds.append(embed)

        await self.message.edit(embeds=embeds, view=self)


def setup(bot):
    bot.add_cog(ARAMCommands(bot))
