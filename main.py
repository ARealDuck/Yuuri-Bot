import os
import sys
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("YUURI_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TEST_GUILD_ID = 939897099024203778

if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    guild = discord.Object(id=TEST_GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)

    print("Slash commands synced")

bot.tree.command(name="Force Restart", description='For if Yuuri misbehaves.')
async def force_restart(interaction: discord.Interaction):
    if not await bot.is_owner(interaction.user):
        await interaction.response.send_message("Hey! Watch it! You cant tell me what to do!", ephemeral=True)
        return
        await interaction.response.send_message("Oh alright Ill do as you say.", ephemeral=True)
        await bot.close()
        sys.exit(0)

bot.run(TOKEN)
