import discord
import random
import asyncio
from discord.ext import commands

class Fun(commands.Cog):

      def __init__(self,client):
        self.client = client

      @commands.command()
      async def pp(self, ctx, member: discord.Member = None):
          if not member:

              response=['=','==','===','====','=====','======','=======','========','=========']
              embed=discord.Embed(title=f'{ctx.author.name}\'s pp\'s size ',
                 description=f"8{random.choice(response)}D",color = 0xdb7bff)
              await ctx.send(embed=embed)
          else:
              response = ['=', '==', '===', '====', '=====', '======', '=======', '========', '=========']
              embed = discord.Embed(title=f'{member.name}\'s pp\'s size ', description=f"8{random.choice(response)}D",
                              color=0xdb7bff)
              await ctx.send(embed=embed)


      @commands.command()
      async def howgay(self, ctx, member: discord.Member = None):
             if not member:
                 response=[random.randint(0,100)]
                 embed=discord.Embed(title='Gay Rating Device!',
                    description=f"\n{ctx.author.mention} is {random.choice(response)}% gay!!  :rainbow_flag:",color = 0xdb7bff)
                 await ctx.send(embed=embed)
             else:
                 response=[random.randint(0,100)]
                 embed=discord.Embed(title='Gay Rating Device!',
                    description=f"\n{member.mention} is {random.choice(response)}% gay!!  :rainbow_flag:",color = 0xdb7bff)
                 await ctx.send(embed=embed)










def setup(client):
    client.add_cog(Fun(client))
