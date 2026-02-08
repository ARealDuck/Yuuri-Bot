import os
import discord
from discord.ext import commands

TOKEN = os.getenv("YUURI_TOKEN")

bot = commands.Bot(command_prefix="/")

bot.run(TOKEN)

if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")
