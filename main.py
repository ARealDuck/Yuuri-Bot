import asyncio
import os
import logging
import sys
import time
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

db = sqlite3.connect("voice_time.db")
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS voice_sessions (
    user_id INTEGER,
    guild_id INTEGER,
    channel_id INTEGER,
    joined_at REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS voice_totals (
    user_id INTEGER,
    guild_id INTEGER,
    total_seconds REAL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
)
""")
db.commit()

# set up bot variables and settings
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
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=94590628721070080)
TEST_GUILD_ID = 939897099024203778
test_guild = discord.Object(id=TEST_GUILD_ID)
TRACKED_CHANNEL_ID = 1470424640470908969
voice_times = {}
if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")


@bot.event
async def on_ready():

    logger.info(f"Logged in as {bot.user}")
    now = time.time()
    cursor.execute("SELECT user_id, guild_id FROM voice_sessions")
    sessions = cursor.fetchall()
    for user_id, guild_id in sessions:
        cursor.execute("""
                UPDATE voice_sessions
                SET joined_at=?
                WHERE user_id=? AND guild_id=?
            """, (now, user_id, guild_id))
    db.commit()
    guild = discord.Object(id=TEST_GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logger.info("Slash commands synced")
    channel = guild.get_channel(TRACKED_CHANNEL_ID)
    if hasattr(bot, "vc_ready"):
        return
    bot.vc_ready = True
    if guild.voice_client:
        return  # already connected.
    await channel.connect()
    logger.info(f"Joined voice channel! {channel.name}")

@bot.event  # Tracking sleep channel contributors.
async def on_voice_state_update(member, before, after):

    # Ignore mutes/deafens/streams/etc
    if before.channel == after.channel:
        return

    now = time.time()
    guild_id = member.guild.id
    user_id = member.id

    # joined tracked channel
    if before.channel is None and after.channel is not None:
        cursor.execute("""
            INSERT OR REPLACE INTO voice_sessions
            (user_id, guild_id, channel_id, joined_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, guild_id, after.channel.id, now))
        db.commit()

    # left tracked channel
    elif before.channel is not None and after.channel is None:
        cursor.execute("""
                SELECT joined_at FROM voice_sessions
                WHERE user_id=? AND guild_id=?
            """, (user_id, guild_id))

        row = cursor.fetchone()
        if not row:
            return

        joined_at = row[0]
        duration = now - joined_at

        # Remove active session
        cursor.execute("""
                DELETE FROM voice_sessions
                WHERE user_id=? AND guild_id=?
            """, (user_id, guild_id))

        # Add to lifetime total
        cursor.execute("""
                INSERT INTO voice_totals (user_id, guild_id, total_seconds)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, guild_id)
                DO UPDATE SET total_seconds = total_seconds + ?
            """, (user_id, guild_id, duration, duration))

        db.commit()


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

@bot.tree.command(name="afk_time", description="Show total afk times")
async def vc_time(interaction: discord.Interaction):
    cursor.execute("""
            SELECT total_seconds FROM voice_totals
            WHERE user_id=? AND guild_id=?
        """, (interaction.user.id, interaction.guild.id))

    row = cursor.fetchone()
    total = row[0] if row else 0

    hours = total // 3600
    minutes = (total % 3600) // 60

    await interaction.response.send_message(
        f"You’ve spent **{int(hours)}h {int(minutes)}m** in voice.",
        ephemeral=True
    )

bot.run(TOKEN)
