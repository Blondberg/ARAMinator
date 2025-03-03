import discord
import os
from dotenv import load_dotenv
import logging
import datetime
import platform
from db.database import init_db

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX")

# Setup logger
araminator_logger = logging.getLogger("araminator")
araminator_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename=f"logs/araminator{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}.log",
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(logging.Formatter("%(asctime)s :: %(levelname)-7s :: %(message)s"))
araminator_logger.addHandler(handler)


discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s :: %(levelname)-7s :: %(message)s"))
discord_logger.addHandler(handler)


console = logging.StreamHandler()
console.setLevel(logging.INFO)
araminator_logger.addHandler(console)

logger = araminator_logger

bot = discord.Bot()

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.members = True

# initialize database
init_db()


EXTENSIONS = ["cogs.player_commands", "cogs.aram_commands"]

# Load in all extensions (cogs)
for extension in EXTENSIONS:
    try:
        logger.debug(f"Loading extension '{extension}'.")
        bot.load_extension(extension)
        logger.debug(f"Extension '{extension}' loaded.")
    except Exception as e:
        logger.exception(e)


@bot.event
async def on_ready():
    """Log platform information and load extensions (cogs) when bot is ready"""
    logger.info(f"Logged in as: {bot.user.name}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"System OS: {platform.system()} {platform.release()}")
    logger.info("Bot is ready!")


@bot.event
async def on_application_command(ctx):
    """Executed before every command. Logs command invoked, author and target guild"""
    logger.debug(
        f"Command invoked '{ctx.command}' in guild {ctx.guild.name} (ID: {ctx.guild.id}) by {ctx.author} (ID: {ctx.author.id})"
    )


# Run the bot
try:
    bot.run(DISCORD_TOKEN, reconnect=True)
except Exception as e:
    logger.error(f"Bot crashed with error: {e}")
    print("An error has occured. Check logs.")
    input("Press Enter to exit")
