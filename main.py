import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os
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
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }]
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

async def get_youtube_source(url):
    info = ytdl.extract_info(url, download=False)
    return info['url'], info['title']

async def play_song(ctx, url, is_slash=False):
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

        voice_client.play(discord.FFmpegPCMAudio(source_url))
        msg = f"Playing **{title}**!"
        
        if is_slash:
            await ctx.followup.send(content=msg)  # Responds with a follow-up message for slash commands
        else:
            await ctx.send(msg)
    else:
        msg = "You need to join a voice channel first!"
        if is_slash:
            await ctx.followup.send(content=msg)
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
    await play_song(interaction, url, is_slash=True)

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

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}!")
    print("Slash commands synced.")

bot.run(DISCORD_TOKEN)

