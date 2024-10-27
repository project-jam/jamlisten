import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
import subprocess
import asyncio
from youtubeSpotifyConverter import youtubeSpotifyConverter

YOUTUBE_API_KEY = os.getenv("YOUTUBE_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

converter = youtubeSpotifyConverter(YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="jam!", intents=intents)
tree = bot.tree

ytdl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }]
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

# Dictionary to store the loop status for each guild
loop_status = {}

async def get_youtube_source(search_term):
    try:
        info = ytdl.extract_info(search_term, download=False)
        if 'entries' in info:
            info = info['entries'][0]

        if 'url' in info and 'title' in info:
            return info['url'], info['title']
        else:
            raise KeyError("Required information ('url' or 'title') is missing in the extracted data.")
    except Exception as e:
        print(f"Error extracting information: {e}")
        return None, None

async def play_song(ctx, url, is_slash=False, interaction=None):
    global loop_status  # Access global loop status
    if isinstance(ctx, commands.Context):
        author_voice = ctx.author.voice
        voice_client = ctx.guild.voice_client
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

        voice_client.play(discord.FFmpegPCMAudio(source_url), after=lambda e: print(f"Finished playing: {title}"))
        voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
        voice_client.source.volume = 0.5  # Adjust the volume as needed

        msg = f"Playing **{title}**!"
        
        if is_slash:
            await interaction.followup.send(content=msg)  # Use interaction here
        else:
            await ctx.send(msg)

        # Wait until the song finishes, and check for loop status
        while voice_client.is_playing() or (loop_status.get(ctx.guild.id, False) and not voice_client.is_playing()):
            await asyncio.sleep(1)  # Wait for 1 second
            
            # If looping is enabled and the song has finished, restart it
            if not voice_client.is_playing() and loop_status.get(ctx.guild.id, False):
                voice_client.play(discord.FFmpegPCMAudio(source_url), after=lambda e: print(f"Finished playing: {title}"))
                await asyncio.sleep(1)  # Short delay before checking again

        # Disconnect after the song finishes if looping is off
        if not loop_status.get(ctx.guild.id, False):
            await voice_client.disconnect()
            if is_slash:
                await interaction.followup.send(f"Disconnected after playing **{title}**!")  # Use interaction here
    else:
        msg = "You need to join a voice channel first!"
        if is_slash:
            await interaction.followup.send(content=msg)  # Use interaction here
        else:
            await ctx.send(msg)

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

async def pause_song(ctx, is_slash=False):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.pause()
        msg = "Paused the music."
    else:
        msg = "No music is currently playing!"
    
    if is_slash:
        await ctx.followup.send(content=msg)
    else:
        await ctx.send(msg)

async def resume_song(ctx, is_slash=False):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        msg = "Resumed the music."
    else:
        msg = "No music is currently paused!"
    
    if is_slash:
        await ctx.followup.send(content=msg)
    else:
        await ctx.send(msg)

@tree.command(name="play", description="Play a song from a URL in the voice channel")
async def play_slash(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await play_song(interaction, url, is_slash=True, interaction=interaction)  # Pass interaction here

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

@bot.command(name="pause")
async def pause(ctx):
    await pause_song(ctx)

@tree.command(name="pause", description="Pause the currently playing music")
async def pause_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    await pause_song(interaction, is_slash=True)

@bot.command(name="resume")
async def resume(ctx):
    await resume_song(ctx)

@tree.command(name="resume", description="Resume the paused music")
async def resume_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    await resume_song(interaction, is_slash=True)

@bot.command(name="loop")
async def loop(ctx):
    # Toggle loop status for the current guild
    loop_status[ctx.guild.id] = not loop_status.get(ctx.guild.id, False)
    status = "enabled" if loop_status[ctx.guild.id] else "disabled"
    await ctx.send(f"Looping is now {status}!")

@bot.command(name="ping")
async def ping(ctx):
    # Get the latency in milliseconds
    latency_ms = round(bot.latency * 1000)
    # Get the region of the server
    server_region = str(ctx.guild.region).capitalize()
    await ctx.send(f"Pong! It's {latency_ms} ms according to {server_region}.")

@bot.command(name="shell")
async def shell(ctx, *, command: str):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()

        if output:
            # Split the output into chunks of 2000 characters or less
            for i in range(0, len(output), 2000):
                await ctx.send(f"```ansi\n{output[i:i + 2000]}\n```")  # Mark as code with ansi
        else:
            await ctx.send("No output returned.")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

@tree.command(name="shell", description="Execute a shell command")
async def shell_slash(interaction: discord.Interaction, command: str):
    await interaction.response.defer()
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip() or result.stderr.strip()
        
        if output:
            for i in range(0, len(output), 2000):
                await interaction.followup.send(f"```ansi\n{output[i:i + 2000]}\n```")  # Mark as code with ansi
        else:
            await interaction.followup.send("No output returned.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}!")
    print("Slash commands synced.")

bot.run(DISCORD_TOKEN)

