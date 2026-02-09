import asyncio
import os
import logging
import sys
import discord
from discord import app_commands
from discord.ext import commands

# set logging
logger = logging.getLogger("YuuriBot")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("yuuribot.log")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
TOKEN = os.getenv("YUURI_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=94590628721070080)

TEST_GUILD_ID = 939897099024203778
test_guild = discord.Object(id=TEST_GUILD_ID)
if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

    guild = discord.Object(id=TEST_GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    logger.info("Slash commands synced")


@bot.tree.command(name="restart_yuuri", description='For if Yuuri misbehaves.', guild=test_guild)
async def force_restart(interaction: discord.Interaction):
    logger.debug("caught force restart command.")
    await interaction.response.defer(ephemeral=True)
    if not await bot.is_owner(interaction.user):
        await interaction.followup.send("Hey! Watch it! You cant tell me what to do!", ephemeral=True)
        return
    await interaction.followup.send("Oh alright Ill do as you say.", ephemeral=True)
    await asyncio.sleep(0.2)
    await bot.close()
    raise SystemExit(0)


bot.run(TOKEN)
