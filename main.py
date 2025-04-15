import asyncio
import os
import random
from datetime import datetime
from time import sleep

import discord
from discord import channel
import inspirobot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import yt_dlp
from discord import FFmpegPCMAudio, guild, permissions, voice_client
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

greet = ['sup', 'yo', 'wassup', 'wsg', 'hello', 'hi', 'hey', 'hola']

queue = {}

ytdl_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'noplaylist': False,
    'quiet': True,
    'source_address': '0.0.0.0',  # Bypass some network issues
    'nocheckcertificate': True,  # Ignore SSL certificate errors
    'geo_bypass': True,  # Avoid regional restrictions
    'geo_bypass_country': 'US',  # Set a default country to bypass geo-blocks
    'youtube_include_dash_manifest': False  # Avoid format extraction issues
}

ffmpeg_options = {
      'options': '-vn'
}

@bot.event
async def on_ready():
  try:
    print(f'{bot.user} has successfully connected')
    activ = discord.Game(name="$help", type=3)
    await bot.change_presence(status=discord.Status.online, activity=activ)
  except Exception as e:
    print(e)


#----BOT-FUNCS----#

@bot.command()
async def ms(ctx):
  await ctx.send(f'``` ping is {round(bot.latency * 1000)}ms ```')


@bot.event
async def on_message(message):

  await bot.process_commands(message)
  if message.author == bot.user:
    return

  await greet_user(message)


@bot.command()
async def deep(ctx):
  quote = inspirobot.generate()
  await ctx.send(quote)
  
@bot.command()
async def vchelp(ctx):
  await ctx.send("https://tenor.com/view/yes-king-gif-15627861872304913213")
  
  help_message = """
    **$join** - Makes the bot join your current vc.
    **$leave** - Makes the bot leave the current vc.
    **$yt <URL>** - Adds a yt video or playlist to the queue and plays it in the vc.
    **$skip** - Skips the currently playing song.
    **$q** - Displays the current queue of songs.
    **$goat** - :goat: :crown: :microphone: 
    **$feta** - :musical_note: :cheese: 
    **$clear** - Clears the current queue.
    **$vchelp** - Displays this help message.
    """
  embed = discord.Embed(
        title="Voice Channel Commands Help",
        description=help_message,
        color=discord.Color.blue()
  )
  embed.set_footer(text="Use these commands to control the bot in voice channels.")
  await ctx.send(embed=embed)


#----VC-FUNCS----#

@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        # Exiting if the bot it's not connected to a voice channel
        return 

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


@bot.command()
async def join(ctx):
  if ctx.author.voice:
    channel = ctx.author.voice.channel
    await channel.connect()
  else:
    await ctx.send("You are not connected to a voice channel.")

@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
  else:
    await ctx.send("I'm not connected to a voice channel.")
    
    
@bot.command()
async def yt(ctx, url:str):
  
  guild_id = ctx.guild.id
  
  if ctx.voice_client is None:
      channel = ctx.author.voice.channel
      await channel.connect()
  else:
      await ctx.send("I am already connected to a voice channel.")
    
  ytdl = yt_dlp.YoutubeDL(ytdl_options)
  
  try:
    info = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    
    if guild_id not in queue:
      queue[guild_id] = []

    if 'entries' in info:
      for entry in info["entries"]:
        audio_url = entry["url"]
        title = entry["title"]
        queue[guild_id].append((audio_url, title))
    else:
      audio_url = info["url"]
      title = info["title"]
      queue[guild_id].append((audio_url, title))

    if not ctx.voice_client.is_playing():
      await play_next(ctx)
  
  except Exception as e:
    await ctx.send(f"Error: {str(e)}")
    

async def play_next(ctx):
  guild_id = ctx.guild.id
  
  if guild_id in queue and queue[guild_id]:
    audio_url, title = queue[guild_id].pop(0)
    ctx.voice_client.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options), after=lambda e: bot.loop.create_task(play_next(ctx)))
    await ctx.send(f"Now playing: {title}")
  
  else:
    await ctx.send("Queue is empty.")
    await ctx.voice_client.disconnect()
    
    
@bot.command()
async def skip(ctx):
  if ctx.voice_client and ctx.voice_client.is_playing():
    ctx.voice_client.stop()
    await ctx.send("Skipped.")
  else:
    await ctx.send("No song is currently playing.")


@bot.command()
async def q(ctx):
  guild_id = ctx.guild.id
  
  if guild_id in queue and queue[guild_id]:
    queue_list = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(queue[guild_id])])
    await ctx.send(f"Queue:\n{queue_list}")
  else:
    await ctx.send("Queue is empty.")
    
@bot.command()
async def clear(ctx):
  guild_id = ctx.guild.id
  
  if guild_id in queue:
    queue[guild_id].clear()
    await ctx.send("Queue cleared.")
  else:
    await ctx.send("Queue is empty.")


@bot.command()
async def preloaded(ctx):
  if ctx.voice_client is None:
    channel = ctx.author.voice.channel
    await channel.connect()
  else:
    url = choose_line("preloaded_songs.txt")
    ytdl = yt_dlp.YoutubeDL(ytdl_options)
    info = ytdl.extract_info(url, download=False)  # Extract video info
    audio_url = info["url"]
    vc = ctx.voice_client
    vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))
    await ctx.send(f"Playing: {info['title']}")

    
#----NON DISC FUNCS----#
def choose_line(file_name):
  with open(file_name, 'r') as file:
    lines = file.readlines()
    random_line = random.choice(lines)
  return random_line


async def greet_user(message):
  if any(word in message.content.lower() for word in greet):
    await message.channel.send("wsg")

TOKEN = "..."
bot.run(TOKEN)
