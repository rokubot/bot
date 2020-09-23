import discord
import os
import random
import time
import asyncio
import aiohttp
import logging

import traceback
import youtube_dl
import sqlite3
from discord.ext import commands

token = open("token.txt", "r").read()

client = commands.Bot(command_prefix=["Ro ","ro ","R!","r!"], case_insensitive=True, help_command=None)
players = {}

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"


@client.event
async def on_ready():
  #please dont do anything in on_ready ....
  game = discord.Game("Ro help")
  await client.change_presence(status=discord.Status, activity=game)
  print(f'logged in as {client.user}')


@client.event
async def on_member_join(member):
   if member.guild.id == 697029214289002536:
     channel = client.get_channel(697029214289002539)
     await channel.send(f'{member.name} has joined the server. Welcome the User! <@&719494944146063391>')



@client.event
async def on_member_remove(member):
  if member.guild.id == 697029214289002536:
    channel = client.get_channel(697029214289002539)
    await channel.send(f'{member.name} has left the server ')
    await channel.send('<a:crying:716427099300429854> ')


@client.command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        client.load_extension(f'cogs.{extension}')
    except Exception as e:
        await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
    else:
        await ctx.send('<:greenTick:724182824621703200> Succesfully Loaded!')



@client.command()
@commands.is_owner()
async def unload(ctx, extension):
    try:
        client.unload_extension(f'cogs.{extension}')
    except Exception as e:
        await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
    else:
        await ctx.send('<:greenTick:724182824621703200> Succesfully Unloaded!')


@client.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        client.reload_extension(f'cogs.{extension}')
    except Exception as e:
        await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
    else:
        await ctx.send('<:greenTick:724182824621703200> Succesfully Reloaded!')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.command()
async def ping(ctx):
 """This mwthod is by Lemon. Gives ping below 0 too :)"""
 mess = await ctx.message.channel.send('🏓 Pong!')
 interval = mess.created_at - ctx.message.created_at
 value = interval.total_seconds() * 1000
 pong = round(value)
 await mess.edit(content=f'🏓 Pong! In {pong} ms')

@client.command(aliases=['hi','hello','Yo','Yahello','sup'])
async def hey(ctx):
    responses = ['Hello! \n:wave:','Hi \n:wave:','Sup?','Hemmo >~<','Ello~']
    await ctx.send(f'{random.choice(responses)}')





@client.command(alaises=['Cry','Cri','Sad'])
async def cry(ctx):
      embed= discord.Embed(title=f'{ctx.author.name} is crying :sob: , My heart is gonna break!! :broken_heart:  ',
      color=0xdb7bff)
      gifs=['https://media1.tenor.com/images/8f6da405119d24f7f86ff036d02c2fd4/tenor.gif?itemid=5378935',
      'https://media1.tenor.com/images/3b1a145fc182fd2b0cbb29d32e37f43b/tenor.gif?itemid=8572836',
      'https://media1.tenor.com/images/e07ff7159c902150890d84329d253931/tenor.gif?itemid=15021750',
      'https://media1.tenor.com/images/67df1dca3260e0032f40048759a967a5/tenor.gif?itemid=5415917',
      'https://media1.tenor.com/images/213ec50caaf02d27d358363016204d1d/tenor.gif?itemid=4553386',
      'https://media1.tenor.com/images/bdd8e3865332d5ccf2edddd1460e0792/tenor.gif?itemid=16786822',
      'https://media1.tenor.com/images/bc6517ddc10fc60c4dc73c9e3a00eafa/tenor.gif?itemid=13995463]',
      'https://tenor.com/view/oh-no-sad-cry-crying-yui-hirasawa-gif-5415917',
      'https://media.tenor.com/images/224221bb396c782daa0333a23a1c4d51/tenor.gif']
      link= random.choice(gifs)
      embed.set_image(url=f'{link}')
      await ctx.send(embed=embed)

@client.command(alaises=['Smile','Happy','Grin'])
async def smile(ctx):
      embed= discord.Embed(title=f'{ctx.author.name} smiles! :grin:  ',
      color=0xdb7bff)
      gifs=['https://cdn.discordapp.com/attachments/697029214289002539/720796063950176286/image0.gif',
      'https://cdn.discordapp.com/attachments/697029214289002539/720796063950176286/image0.gif',
      'https://images-ext-1.discordapp.net/external/Qj9mj2E1YDcVTespi0Vfig-RiaAc7N0uy88Q0IahBng/https://cdn.weeb.sh/images/rkH84ytPZ.gif?width=400&height=225',
      'https://media.discordapp.net/attachments/697029214289002539/721016708776722574/image0.gif',
      'https://cdn.discordapp.com/attachments/719560200897691728/721351702808363008/image0.gif',
      'http://pa1.narvii.com/6339/ad70e90381a8a5bf9b59657feb86e0bc34108b59_hq.gif?size=450x320']
      link= random.choice(gifs)
      embed.set_image(url=f'{link}')
      await ctx.send(embed=embed)
@client.event
async def on_message(message):

# Dont mind these lol, all these code were made when i was beginner to dpy and python
 if message.content.startswith('Ro snd'):
  arg = message.content.split(' ')
  id = int(arg[2])
  ch = client.get_channel(id)
  mess = f'{message.content}'
  filt = mess.replace('Ro snd', '')
  filt2 = filt.replace(f'{arg[2]}', '')
  await ch.send(filt2)



 if message.content.startswith(''):
  if message.guild is None:
   mess = f'{message.author.name} said : {message.content}'
   ch = client.get_channel(724579909745377342)
   await ch.send(str(mess))


 if message.content.startswith('Ro slap'):
    arg = message.content.split(' ')
    if arg[0] == 'Ro' and arg[1] == 'slap':
     mention = message.mentions
     e = discord.Embed(title=f'{message.author.display_name} slapped {mention[0].display_name} very hard!! ' , color = 0xdb7bff)
     content = ['https://i.imgur.com/fm49srQ.gif', 'https://i.imgur.com/CwbYjBX.gif', 'https://i.imgur.com/oRsaSyU.gif','https://cdn.lowgif.com/medium/0435c1d443ee667e-.gif',
     'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b02c16d5-1b1b-4139-92e6-ca6b3d768d7a/d6wv007-5fbf8755-5fca-4e12-b04a-ab43156ac7d4.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOiIsImlzcyI6InVybjphcHA6Iiwib2JqIjpbW3sicGF0aCI6IlwvZlwvYjAyYzE2ZDUtMWIxYi00MTM5LTkyZTYtY2E2YjNkNzY4ZDdhXC9kNnd2MDA3LTVmYmY4NzU1LTVmY2EtNGUxMi1iMDRhLWFiNDMxNTZhYzdkNC5naWYifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6ZmlsZS5kb3dubG9hZCJdfQ.u7RPUGC0FivWZl_hS-5vdlqDLpkAaHbGps9ejNTUKos']
     link = random.choice(content)
     e.set_image(url=f'{link}')
     await message.channel.send(embed=e)

 if message.content.startswith('Ro cuddle'):
    arg = message.content.split(' ')
    if arg[0] == 'Ro' and arg[1] == 'cuddle':
     mention = message.mentions
     e = discord.Embed(title=f'{message.author.display_name} cuddles {mention[0].display_name} , so cute >~< ' , color = 0xdb7bff)
     content = ['https://media1.tenor.com/images/8f8ba3baeecdf28f3e0fa7d4ce1a8586/tenor.gif?itemid=12668750', 'https://i.imgur.com/VNhuTUT.gif',
     'https://media1.tenor.com/images/e07473d3cf372dbc24c760527740b85e/tenor.gif?itemid=12668884', 'https://media1.tenor.com/images/08de7ad3dcac4e10d27b2c203841a99f/tenor.gif?itemid=4885268']
     link = random.choice(content)
     e.set_image(url=f'{link}')
     await message.channel.send(embed=e)

 await client.process_commands(message)

@client.command(name='logout', aliases=['shutdown'])
@commands.is_owner()
async def botstop(ctx):
    """Turn your bot off"""
    await ctx.send('Goodbye')
    await client.logout()
client.run(token)
