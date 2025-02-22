import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import logging
import datetime
import platform 

load_dotenv()
DISCORD_TOKEN=os.getenv("DISCORD_TOKEN")
BOT_PREFIX=os.getenv("BOT_PREFIX")

# Setup logger
logger = logging.getLogger("araminator")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename=f"logs/araminator{datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")}.log",
    encoding="utf-8",
    mode="w",
)
handler.setFormatter(logging.Formatter("%(asctime)s :: %(levelname)-7s :: %(message)s"))
logger.addHandler(handler)

bot = discord.Bot()
intents = discord.Intents.default()
intents.message_content = True
intents.typing = True
intents.members = True

EXTENSIONS = []

@bot.event
async def on_ready():
    """"Log platform information and load extensions (cogs) when bot is ready"""
    print(f"Logged in as: {bot.user.name}")
    print(f"Python version: {platform.python_version()}")
    print(f"System OS: {platform.system()} {platform.release()}")
    logger.info(f"Logged in as: {bot.user.name}")
    logger.info(f"Python version: {platform.python_version()}")
    logger.info(f"System OS: {platform.system()} {platform.release()}")
    
    # Load in all extensions (cogs)
    for extension in EXTENSIONS:
        try:
            await bot.load_extension(extension)
            logger.debug(f"Loading extension '{extension}'.")
            bot.load_extension(f"cogs.{extension}")
            logger.debug(f"Extension '{extension}' loaded.")
        except Exception as e: 
            logger.error(e)

    logger.info("Bot is ready!")


@bot.event
async def on_application_command(ctx): 
    """Executed before every command

    Args:
        ctx (commands.Context): Context of the command
    """
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