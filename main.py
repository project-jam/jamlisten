import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
from youtubeSpotifyConverter import youtubeSpotifyConverter

# Replace with your actual keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Instantiate a youtubeSpotifyConverter object
converter = youtubeSpotifyConverter(YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="jam!", intents=intents)
tree = bot.tree  # For handling slash commands

# YTDL options for YouTube audio extraction
ytdl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }]
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

# Function to extract YouTube audio source
async def get_youtube_source(url):
    info = ytdl.extract_info(url, download=False)
    return info['url'], info['title']

# Function to play a song
async def play_song(ctx, url, is_slash=False):
    if isinstance(ctx, commands.Context):
        author_voice = ctx.author.voice
        voice_client = ctx.guild.voice_client
    else:  # It's an Interaction
        author_voice = ctx.user.voice
        voice_client = ctx.guild.voice_client
    
    if author_voice and author_voice.channel:
        voice_channel = author_voice.channel
        # Connect to the voice channel if not already connected
        if not voice_client:
            voice_client = await voice_channel.connect()

        # Convert Spotify URL to YouTube if necessary
        if "spotify.com" in url:
            links = converter.C_fromLink(url)
            url = links.get('youtube', url)  # Default to original URL if conversion fails

        # Fetch YouTube audio source
        source_url, title = await get_youtube_source(url)
        
        # Ensure the voice client is still valid before stopping and playing
        if voice_client.is_playing():
            voice_client.stop()  # Stop any current song
        
        # Play the song
        voice_client.play(discord.FFmpegPCMAudio(source_url))
        
        # Edit response instead of sending a new message
        msg = f"Playing **{title}**!"
        if is_slash:
            await ctx.edit_original_response(content=msg)
        else:
            await ctx.send(msg)
    else:
        msg = "You need to join a voice channel first!"
        if is_slash:
            await ctx.edit_original_response(content=msg)
        else:
            await ctx.send(msg)

# Function to stop playback and leave the voice channel
async def stop_song(ctx, is_slash=False):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        if is_slash:
            await ctx.edit_original_response(content="Stopped the music and left the voice channel.")
        else:
            await ctx.send("Stopped the music and left the voice channel.")
    else:
        msg = "I'm not currently in a voice channel!"
        if is_slash:
            await ctx.edit_original_response(content=msg)
        else:
            await ctx.send(msg)

# Function to pause the current playback
async def pause_song(ctx, is_slash=False):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.pause()
        if is_slash:
            await ctx.edit_original_response(content="Paused the music.")
        else:
            await ctx.send("Paused the music.")
    else:
        msg = "No music is currently playing!"
        if is_slash:
            await ctx.edit_original_response(content=msg)
        else:
            await ctx.send(msg)

# Function to resume playback
async def resume_song(ctx, is_slash=False):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        if is_slash:
            await ctx.edit_original_response(content="Resumed the music.")
        else:
            await ctx.send("Resumed the music.")
    else:
        msg = "No music is currently paused!"
        if is_slash:
            await ctx.edit_original_response(content=msg)
        else:
            await ctx.send(msg)

# Slash command to play a song
@tree.command(name="play", description="Play a song from a URL in the voice channel")
async def play_slash(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await play_song(interaction, url, is_slash=True)

# Prefix command to play a song
@bot.command(name="play")
async def play(ctx, url: str):
    await play_song(ctx, url)

# Command to stop playback
@bot.command(name="stop")
async def stop(ctx):
    await stop_song(ctx)

@tree.command(name="stop", description="Stop the music and leave the voice channel")
async def stop_slash(interaction: discord.Interaction):
    await stop_song(interaction, is_slash=True)

# Command to pause playback
@bot.command(name="pause")
async def pause(ctx):
    await pause_song(ctx)

@tree.command(name="pause", description="Pause the currently playing music")
async def pause_slash(interaction: discord.Interaction):
    await pause_song(interaction, is_slash=True)

# Command to resume playback
@bot.command(name="resume")
async def resume(ctx):
    await resume_song(ctx)

@tree.command(name="resume", description="Resume the paused music")
async def resume_slash(interaction: discord.Interaction):
    await resume_song(interaction, is_slash=True)

# Event handler for bot startup
@bot.event
async def on_ready():
    await tree.sync()  # Sync slash commands with Discord
    print(f"Logged in as {bot.user}!")
    print("Slash commands synced.")

# Run the bot
bot.run(os.getenv("DISCORD_TOKEN"))

