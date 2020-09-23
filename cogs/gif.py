import aiohttp
import json
import random
import asyncio
from discord.ext import commands
import discord
class Gif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1,10,commands.BucketType.user)
    async def hug(self,ctx,member:discord.Member):
      #do stuffs here
    @hug.error
    async def hug_error(self,ctx,error):
        if isinstance(error,commands.CommandOnCooldown):
         await ctx.send(f"*`You're on cooldown,please wait {round(error.retry_after)} seconds to use this command again`*")
        else:
            raise(error)

    @commands.command(alaises=['pet'])
    @commands.cooldown(1,10,commands.BucketType.user)
    async def pat(self,ctx,member:discord.Member):
        #do stuffs here

    @pat.error
    async def pat_error(self,ctx,error):
        if isinstance(error,commands.CommandOnCooldown):
            await ctx.send(f"*`You're on cooldown,please wait {round(error.retry_after)} seconds to use to use this command again`*")
        else:
            raise(error)
    @commands.command()
    @commands.cooldown(1,10,commands.BucketType.user)
    async def meme(self,ctx):
        #use reddit json api
    @meme.error
    async def meme_error(self,ctx,error):
        if isinstance(error,commands.CommandOnCooldown):
            msg=await ctx.send(f"*`You're on cooldown,please wait {round(error.retry_after)} seconds to use to use this command again`*")
            await asyncio.sleep(5)
            await message.delete()
        else:
            raise(error)

    @commands.command(alaises=['pfp','picture','display picture'])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        e = discord.Embed(title=f"{member.name}'s avatar" , color = 0xdb7bff)
        e.set_image(url=f'{member.avatar_url}')
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1,10,commands.BucketType.user)
    async def cuddle(self,ctx,member:discord.Member):
        """Cuddles the mentioned user"""
        if ctx.author == member:
            await ctx.send('How do you plan to cuddle yourself? :thinking:')
        else:
            e = discord.Embed(title=f'{ctx.author.name} cuddles {member.name} , so cute >~< ' , color = 0xdb7bff)
            content = ['https://media1.tenor.com/images/8f8ba3baeecdf28f3e0fa7d4ce1a8586/tenor.gif?itemid=12668750', 'https://i.imgur.com/VNhuTUT.gif',
            'https://media1.tenor.com/images/e07473d3cf372dbc24c760527740b85e/tenor.gif?itemid=12668884', 'https://media1.tenor.com/images/08de7ad3dcac4e10d27b2c203841a99f/tenor.gif?itemid=4885268'
            'https://i.pinimg.com/originals/d8/7c/5c/d87c5cdd0a68caf2b6feeec0f7da7315.gif']
            link = random.choice(content)
            e.set_image(url=f'{link}')
            await ctx.send(embed=e)






def setup(bot):
    bot.add_cog(Gif(bot))
