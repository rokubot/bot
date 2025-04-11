import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional, Union

import discord
import humanize
from discord.ext import commands, tasks

from config import color, cross, tick
from ext.converter import SimpleTimeConverter


class Giveaway(commands.Cog):
    """Organize fun and highly customizable giveaways for your server"""

    def __init__(self, bot):
        self.bot = bot
        self.emoji = "🎊"
        self.timer_update.start()
        self.gw_end = self.bot.loop.create_task(self.end_giveaway())
        self.gw_delete = self.bot.loop.create_task(self.delete_giveaway())
        self.giveaway_ended = {}

    def cog_unload(self):
        self.timer_update.cancel()
        self.gw_end.cancel()
        self.gw_delete.cancel()

    async def delete_giveaway(self):
        """Deleted Giveaways after 2 days of its End Time"""

        await self.bot.wait_until_ready()
        self.bot.logger.info('[Giveaway] Starting Giveaway delete task')
        giveaways = self.bot.db.giveaways.find({'ended': True})
        async for result in giveaways:
            timestamp = result['timestamp']
            pastdate = datetime.utcnow() - timedelta(days=2)

            if pastdate > timestamp:
                await self.bot.db.giveaways.delete_one(result)

    async def end_giveaway(self):
        """Task to end giveaway on bot restart"""

        await self.bot.wait_until_ready()
        self.bot.logger.info('[Giveaway] Starting Giveaway end task')
        giveaways = self.bot.db.giveaways.find({'ended': False})
        async for result in giveaways:
            timestamp = result['timestamp']
            await discord.utils.sleep_until(when=timestamp)

            guild = self.bot.get_guild(result['guild'])
            if guild is None:
                return

            channel = guild.get_channel(result['channel'])
            msg = channel.get_partial_message(result['_id'])
            prize = result['prize']
            winners = result['winners']
            host = result['host']
            ended = result['ended']
            if not ended:
                self.bot.loop.create_task(
                    self.giveaway_task(
                        channel=channel, timestamp=timestamp, msg=msg, winners=winners, host=host, prize=prize, cmd=True
                    )
                )

    def before_embed(self, timestamp, prize, winners, host):
        """The embed before Giveaway"""

        embed = discord.Embed(color=color, timestamp=timestamp)
        embed.description = f"**Prize:** {prize} \n**Winner(s):** {winners} \n**Hosted by:** <@{host}> \n"
        embed.description += f"**Time Remaining:** {humanize.precisedelta(timestamp - datetime.utcnow())}"
        embed.set_footer(text="Giveaway ends at ")

        return embed

    def after_embed(self, timestamp, prize, winners, host):
        """The embed after Giveaway"""

        embed = discord.Embed(color=color, timestamp=timestamp)
        embed.description = f"**Prize:** {prize} \n**Winner(s):** {winners} \n**Hosted by:** <@{host}> \n"
        embed.set_footer(text="Ended at")

        return embed

    async def giveaway_task(self, channel, timestamp, msg, winners, host, prize, cmd=False):
        """Sleeps and ends the giveaway"""

        await discord.utils.sleep_until(when=timestamp)
        msg = await channel.fetch_message(msg.id)

        ended = self.giveaway_ended.get(msg.id, False)
        if cmd and ended:
            return

        reactions = [r for r in msg.reactions if r.emoji == "🎉"]
        users = [user async for user in reactions[0].users()]
        users = [m for m in users if not m.bot]
        y = []

        try:
            for x in range(winners):
                a = random.choice(users)
                users.remove(a)
                y.append(a.mention)

        except IndexError:
            await self.bot.db.giveaways.update_one({'_id': msg.id}, {"$set": {'ended': True}})
            return await channel.send("No one joined the giveaway. ")

        if len(y) > 1:
            a = y.pop()
            winners = f"{', '.join(y)} and {a}"

        elif len(y) == 0:
            await self.bot.db.giveaways.update_one({'_id': msg.id}, {"$set": {'ended': True}})
            return await channel.send('No users found')

        else:
            winners = y[0]

        await channel.send(f"🎉 Congratulations! {winners} has won **{prize}**.\n {msg.jump_url}")
        embed = self.after_embed(timestamp=timestamp, prize=prize, winners=winners, host=host)
        await msg.edit(content="🎉 **GIVEAWAY** 🎉", embed=embed)
        await self.bot.db.giveaways.update_one({'_id': msg.id}, {"$set": {'ended': True}})
        self.giveaway_ended[msg.id] = True

        return

    @tasks.loop(seconds=60)
    async def timer_update(self):
        giveaways = self.bot.db.giveaways.find({'ended': False})
        async for result in giveaways:
            guild = self.bot.get_guild(result['guild'])
            if guild is None:
                return

            channel = self.bot.get_channel(result['channel'])
            msg = channel.get_partial_message(result['_id'])

            timestamp = result['timestamp']
            prize = result['prize']
            winners = result['winners']
            host = result['host']
            ended = result['ended']
            if not ended:
                embed = self.before_embed(timestamp=timestamp, prize=prize, winners=winners, host=host)
                await msg.edit(content="🎉 **GIVEAWAY** 🎉", embed=embed)

    @timer_update.before_loop
    async def timer_update_wait(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(aliases=['giveawaystart', 'gw', 'gastart'])
    @commands.bot_has_permissions(add_reactions=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def gstart(self, ctx, time: SimpleTimeConverter, winners, *, prize):
        """Start a quick Giveaway"""
        try:
            winners = int(winners.lower().split('w')[0])
        except ValueError:
            usage = f"{ctx.prefix}[time][winners][prize]"
            example = f"`{ctx.prefix}gstart 3h 1W Nitro Classic`"
            fmt = f"\n\n**__Command Usage:__** {usage} \n**__Example:__** {example}"
            raise commands.BadArgument(f'You have provided invalid winners. {fmt}')

        if time <= 10:
            return await ctx.send('Giveaway cannot be less than 10 seconds')

        if winners > 55:
            raise commands.BadArgument("You cannot have more than 50 winners.")

        timestamp = datetime.utcnow() + timedelta(seconds=time)
        embed = self.before_embed(timestamp, prize, winners, ctx.author.id)

        msg = await ctx.send("🎉 **GIVEAWAY** 🎉", embed=embed)
        await msg.add_reaction("🎉")
        await ctx.bot.db.giveaways.insert_one(
            {
                '_id': msg.id,
                'channel': ctx.channel.id,
                'guild': ctx.guild.id,
                'timestamp': timestamp,
                'prize': prize,
                'winners': winners,
                'host': ctx.author.id,
                'ended': False,
            }
        )
        self.bot.loop.create_task(
            self.giveaway_task(
                channel=ctx.channel, timestamp=timestamp, msg=msg, winners=winners, host=ctx.author.id, prize=prize, cmd=True
            )
        )

    @commands.hybrid_command()
    @commands.has_guild_permissions(manage_guild=True)
    async def gend(self, ctx, channel: Optional[discord.TextChannel], message):
        """Ends the Giveaway
        You need to pass message ID of the giveaway
        You can also refer (reply) to giveaway embed to end that particular giveaway
        If message ID , link or reference is not given, then it ends the last giveaway event."""

        result = await ctx.bot.db.giveaways.find_one({'_id': message.id})
        if result is None:
            raise commands.BadArgument("That Giveaway doesn't exist or might be an old giveaway")

        ended = result['ended']

        if not ended:
            winners = result['winners']
            host = result['host']
            prize = result['prize']

            self.bot.loop.create_task(
                self.giveaway_task(
                    channel=message.channel,
                    timestamp=datetime.utcnow(),
                    msg=message,
                    winners=winners,
                    host=host,
                    prize=prize,
                )
            )

        else:
            await ctx.send("The Giveaway has ended already")

    @commands.hybrid_command()
    @commands.has_guild_permissions(manage_guild=True)
    async def groll(self, ctx: commands.Context, channel: Optional[discord.TextChannel], message):
        """Reroll the Giveaway.
        You need to pass message ID of the giveaway
        You can also refer (reply) to giveaway embed to end that particular giveaway
        If message ID , link or reference is not given, then it ends the last giveaway event."""

        result = await ctx.bot.db.giveaways.find_one({'_id': message.id})
        if result is None:
            raise commands.BadArgument("That Giveaway doesn't exist or might be an old giveaway")

        winners = result['winners']
        host = result['host']
        prize = result['prize']

        self.bot.loop.create_task(
            self.giveaway_task(
                channel=message.channel, timestamp=datetime.utcnow(), msg=message, winners=winners, host=host, prize=prize
            )
        )


def setup(bot):
    bot.add_cog(Giveaway(bot))
    bot._BotBase__cogs['giveaways'] = bot.get_cog('giveaway')
