import os
import sys
import discord
from discord.ext import commands

TOKEN = os.getenv("YUURI_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")


bot.command(description='For if Yuuri misbehaves.')
async def force_restart(ctx):
    if bot.is_owner(ctx):
        await ctx.send("force restart command received. restarting...")
        await bot.close()
        sys.exit(0)
    else:
        await ctx.send("Hey! Watch it! You cant tell me what to do!")

bot.run(TOKEN)
