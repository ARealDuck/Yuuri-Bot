import asyncio
import os
import logging
import sys
import time
import sqlite3
import discord
from discord import app_commands
from discord.ext import commands, tasks

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
# Settings you can change are here
GUILD_ID = 1140737209436209352  # Server you want the bot to be in.
TRACKED_CHANNEL_ID = 1470424640470908969  # voice channel in said server you want the bot to sleep in
file_handler = logging.FileHandler("yuuribot.log")  # file name for the log
# set up bot variables and settings
logger = logging.getLogger("YuuriBot")
logger.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
TOKEN = os.getenv("YUURI_TOKEN")
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=94590628721070080)
test_guild = discord.Object(id=GUILD_ID)
voice_times = {}
if TOKEN is None:
    raise RuntimeError("RUNTIME ERROR CODE1: Discord Token not found in the environment variable!")
@tasks.loop(seconds=60)
async def check_voice_connection():
    logger.info("Checking if Bot has been disconnected from the tracked channel...")
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        logger.error("Server is not found! this could be due to discord servers being down!")
        return

    voice_client = guild.voice_client

    # if not connected, reconnect.
    if voice_client is None or not voice_client.is_connected():
        channel = guild.get_channel(TRACKED_CHANNEL_ID)
        logger.info(f"Bot is in fact not no longer connected to {channel.name}! attempting to reconnect...")
        if channel and isinstance(channel, discord.VoiceChannel):
            await channel.connect()
            logger.debug(f"Successfully reconnected to {channel.name}")

@bot.event
async def on_ready():
    # stop double execution
    if hasattr(bot, "vc_ready"):
        logger.debug("on_ready already ran once - Skipping...")
        return
    bot.vc_ready = True

    logger.debug(f"Guilds cached: {[g.name for g in bot.guilds]}")
    logger.info(f"Logged in as {bot.user}")

    # DB reset
    now = time.time()
    logger.info("Setting up time DB after restart.")
    cursor.execute("SELECT user_id, guild_id FROM voice_sessions")
    sessions = cursor.fetchall()
    for user_id, guild_id in sessions:
        cursor.execute("""
                UPDATE voice_sessions
                SET joined_at=?
                WHERE user_id=? AND guild_id=?
            """, (now, user_id, guild_id))
    db.commit()

    # Guilds
    logger.info("Syncing commands.")
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        logger.error("Guild not found in cache")
        return

    # Syncing commands
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    logger.info("Slash commands synced")

    # Get voice channel and log in
    logger.debug("Getting Channel.")
    channel = guild.get_channel(TRACKED_CHANNEL_ID)
    if not channel:
        logger.error("Channel not found!")
        return
    logger.debug(f"Got channel! {channel.name}. Moving to next step.")
    logger.debug("Checking if channel is a voice channel.")
    if not isinstance(channel, discord.VoiceChannel):
        logger.error("Channel is not a voice channel! please check if channel id is pointing to the right channel!")
        return
    logger.debug("Channel is in fact a voice channel! Moving to next step.")
    logger.info(f"Attempting to join {channel.name}")
    try:
        await channel.connect()
    except Exception as e:
        logger.exception("Failed to connect to voice channel!")
    logger.info(f"Joined voice channel! {channel.name}")
    check_voice_connection.start()

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

@bot.tree.command(name="afk_time", description="Show total afk times (CURRENTLY BROKEN.)")
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
