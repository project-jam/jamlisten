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

# Global options for yt-dlp
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

# Store each guild's music state in a dictionary
guild_music_state = {}

class GuildMusicState:
    def __init__(self):
        self.loop = False
        self.current_song = None
        self.voice_client = None
        self.is_playing = False

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

async def play_song(ctx, url, is_slash=False, loop=False):
    guild_id = ctx.guild.id
    if guild_id not in guild_music_state:
        guild_music_state[guild_id] = GuildMusicState()
    
    music_state = guild_music_state[guild_id]
    author_voice = ctx.author.voice if isinstance(ctx, commands.Context) else ctx.user.voice
    voice_client = music_state.voice_client

    if author_voice and author_voice.channel:
        voice_channel = author_voice.channel
        if not voice_client:
            music_state.voice_client = await voice_channel.connect()
        
        if "spotify.com" in url:
            links = converter.C_fromLink(url)
            url = links.get('youtube', url)

        source_url, title = await get_youtube_source(url)
        if not source_url:
            msg = "Couldn't fetch the audio source!"
            if is_slash:
                await ctx.followup.send(content=msg)
            else:
                await ctx.send(msg)
            return

        def after_playing(error=None):
            if error:
                print(f"Player error: {error}")
            elif music_state.loop:
                # Play the song again if looping
                play_song(ctx, url, is_slash, loop=True)
            else:
                # Disconnect and notify after song completion
                bot.loop.create_task(ctx.send("Song finished! Disconnecting..."))
                bot.loop.create_task(music_state.voice_client.disconnect())
                del guild_music_state[guild_id]

        if music_state.voice_client.is_playing():
            music_state.voice_client.stop()

        music_state.voice_client.play(discord.FFmpegPCMAudio(source_url), after=after_playing)
        music_state.current_song = title
        music_state.is_playing = True
        music_state.loop = loop

        msg = f"Playing **{title}**!" + (" (Looping)" if loop else "")
        if is_slash:
            await ctx.followup.send(content=msg)
        else:
            await ctx.send(msg)
    else:
        msg = "You need to join a voice channel first!"
        if is_slash:
            await ctx.followup.send(content=msg)
        else:
            await ctx.send(msg)

@bot.command(name="play")
async def play(ctx, url: str):
    await play_song(ctx, url)

@tree.command(name="play", description="Play a song from a URL in the voice channel")
async def play_slash(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await play_song(interaction, url, is_slash=True)

@bot.command(name="loop")
async def toggle_loop(ctx):
    guild_id = ctx.guild.id
    if guild_id in guild_music_state:
        music_state = guild_music_state[guild_id]
        music_state.loop = not music_state.loop
        await ctx.send(f"Looping is now {'enabled' if music_state.loop else 'disabled'}.")
    else:
        await ctx.send("Nothing is playing to loop.")

@tree.command(name="loop", description="Toggle looping for the current song")
async def toggle_loop_slash(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    await interaction.response.defer()
    if guild_id in guild_music_state:
        music_state = guild_music_state[guild_id]
        music_state.loop = not music_state.loop
        await interaction.followup.send(f"Looping is now {'enabled' if music_state.loop else 'disabled'}.")
    else:
        await interaction.followup.send("Nothing is playing to loop.")

@bot.command(name="stop")
async def stop(ctx):
    guild_id = ctx.guild.id
    if guild_id in guild_music_state:
        music_state = guild_music_state[guild_id]
        if music_state.voice_client:
            await music_state.voice_client.disconnect()
            await ctx.send("Stopped the music and left the voice channel.")
            del guild_music_state[guild_id]
    else:
        await ctx.send("I'm not currently in a voice channel!")

@tree.command(name="stop", description="Stop the music and leave the voice channel")
async def stop_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    await stop(interaction)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}!")
    print("Slash commands synced.")

bot.run(DISCORD_TOKEN)

