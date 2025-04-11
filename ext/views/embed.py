import discord
from discord.ext import commands


class EmbedBuilder:
    async def create(self, ctx: commands.Context):
        embed = discord.Embed()
