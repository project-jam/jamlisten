import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import subprocess
import asyncio
from youtubeSpotifyConverter import youtubeSpotifyConverter
from flask import Flask, send_from_directory
import re

YOUTUBE_API_KEY = os.getenv("YOUTUBE_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AUTHORIZED_USER_ID = 756529025719074846  # Replace with your user ID

converter = youtubeSpotifyConverter(YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="jam!", intents=intents)
tree = bot.tree

cookies_path = 'cookies.txt'
ytdl_opts = {
    'format': 'bestaudio/best',
    'geo_bypass': True,
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
    'cookiefile': cookies_path,
    'force_ipv4': True,
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

loop_status = {}

# Utility function to remove ANSI codes for cleaner output in Discord
def clean_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)

# Text-splitting function to handle long outputs
def split_output(output, limit=2000):
    return [output[i:i + limit] for i in range(0, len(output), limit)]

async def get_youtube_source(search_term):
    try:
        info = ytdl.extract_info(search_term, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info.get('url'), info.get('title')
    except Exception as e:
        print(f"Error extracting information: {e}")
        return None, None

async def play_song(ctx, url, is_slash=False, interaction=None):
    if isinstance(ctx, commands.Context):
        author_voice = ctx.author.voice
    else:
        author_voice = ctx.user.voice
    voice_client = ctx.guild.voice_client

    if author_voice and author_voice.channel:
        voice_channel = author_voice.channel
        if not voice_client:
            voice_client = await voice_channel.connect()

        if "spotify.com" in url:
            links = converter.C_fromLink(url)
            url = links.get('youtube', url)

        source_url, title = await get_youtube_source(url)

        if voice_client.is_playing():
            voice_client.stop()

        def after_play(err):
            if err:
                print(f"Playback error: {err}")
            # Only stop playback here; no disconnection or force termination.
            if voice_client and voice_client.is_connected():
                voice_client.stop()

        # Play the audio source
        voice_client.play(discord.FFmpegPCMAudio(source_url), after=after_play)
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = 0.5

        msg = f"Playing **{title}**!"
        if is_slash:
            await interaction.followup.send(content=msg)
        else:
            await ctx.send(msg)

        # Wait for playback to finish or loop if set
        while voice_client.is_playing():
            await asyncio.sleep(1)
    else:
        msg = "You need to join a voice channel first!"
        if is_slash:
            await interaction.followup.send(content=msg)
        else:
            await ctx.send(msg)

@bot.command(name="pause")
async def pause(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("No audio is currently playing.")

@bot.command(name="resume")
async def resume(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("The audio is not paused.")

async def stop_song(ctx, is_slash=False):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        msg = "Stopped the music and left the voice channel."
    else:
        msg = "I'm not currently in a voice channel!"

    if is_slash:
        await ctx.followup.send(content=msg)
    else:
        await ctx.send(msg)

@tree.command(name="play", description="Play a song from a URL in the voice channel")
async def play_slash(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await play_song(interaction, url, is_slash=True, interaction=interaction)

@bot.command(name="play")
async def play(ctx, url: str):
    await play_song(ctx, url)

@bot.command(name="stop")
async def stop(ctx):
    await stop_song(ctx)

@tree.command(name="stop", description="Stop the music and leave the voice channel")
async def stop_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    await stop_song(interaction, is_slash=True)

@bot.command(name="loop")
async def loop(ctx):
    loop_status[ctx.guild.id] = not loop_status.get(ctx.guild.id, False)
    status = "enabled" if loop_status[ctx.guild.id] else "disabled"
    await ctx.send(f"Looping is now {status}!")

@bot.command(name="ping")
async def ping(ctx):
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"Pong! {latency_ms} ms.")

@bot.command(name="shell")
async def shell(ctx, *, command: str):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("You do not have permission to run this command.")
        return

    # Check if the command contains `sudo`
    if "sudo" in command:
        await ctx.send("Please provide the sudo password. Respond with the password:")
        
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        
        try:
            # Wait for the user to send the password
            password_msg = await bot.wait_for('message', check=check, timeout=60)
            password = password_msg.content.strip()

            # Add the password to the sudo command
            command_with_password = f"echo {password} | {command}"

            # Execute the command
            result = subprocess.run(command_with_password, shell=True, capture_output=True, text=True)
            output = result.stdout.strip() or result.stderr.strip()

            # Clean ANSI codes for better readability in Discord
            output_cleaned = clean_ansi_codes(output)

            # Send each chunk of output as a separate message
            for chunk in split_output(output_cleaned):
                await ctx.send(f"```\n{chunk}\n```")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to provide the password. Command cancelled.")
    else:
        # If no sudo required, just run the command directly
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout.strip() or result.stderr.strip()

            # Clean ANSI codes for better readability in Discord
            output_cleaned = clean_ansi_codes(output)

            # Send each chunk of output as a separate message
            for chunk in split_output(output_cleaned):
                await ctx.send(f"```\n{chunk}\n```")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

@tree.command(name="shell", description="Execute a shell command")
async def shell_slash(interaction: discord.Interaction, command: str):
    if interaction.user.id != AUTHORIZED_USER_ID:
        await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
        return

    await interaction.response.defer()  # Defer response to allow processing time
    if "sudo" in command:  # Check if the command contains "sudo"
        await interaction.followup.send("This command requires sudo. Please provide your password.")
        
        # Wait for user to reply with password
        try:
            def check(msg):
                return msg.author == interaction.user and isinstance(msg.channel, discord.TextChannel)

            # Wait for user to respond with the password (with a timeout of 60 seconds)
            msg = await bot.wait_for('message', timeout=60.0, check=check)

            password = msg.content.strip()

            # If a password is provided, run the command with the password
            result = subprocess.run(f"echo {password} | sudo -S {command}", shell=True, capture_output=True, text=True)
            output = result.stdout.strip() or result.stderr.strip()

            # Clean ANSI codes for better readability in Discord
            output_cleaned = clean_ansi_codes(output)

            # Send each chunk of output as a separate message
            for chunk in split_output(output_cleaned):
                await interaction.followup.send(f"```\n{chunk}\n```")
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to provide the password. Command cancelled.", ephemeral=True)
    else:
        # If no sudo required, just run the command directly
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout.strip() or result.stderr.strip()

            # Clean ANSI codes for better readability in Discord
            output_cleaned = clean_ansi_codes(output)

            # Send each chunk of output as a separate message
            for chunk in split_output(output_cleaned):
                await interaction.followup.send(f"```\n{chunk}\n```")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Run the bot
bot.run(DISCORD_TOKEN)
