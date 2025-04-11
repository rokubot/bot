import sys
import traceback
from datetime import timedelta
from io import StringIO
from typing import Union

import discord
import humanize
from discord.ext import commands, menus

from config import bug_webhook, color, cross
from ext.views import ViewError, ViewTimeoutError

BUG_FORUM = 1149890202236633158


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.posts = set()

    def cog_unload(self):
        self.posts.clear()

    async def error_thingy(self, ctx, error_message, usage_bool: bool = False, emoji: str = ""):
        usage = ''
        if usage_bool:
            usage = f"**Usage:** `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`"

        try:
            await ctx.send(f"{emoji} {error_message} \n\n {usage}", allowed_mentions=discord.AllowedMentions.none())

        except (discord.HTTPException, discord.Forbidden) as error:
            text = error.text
            try:
                await ctx.author.send(text)
            except discord.HTTPException:
                pass

    @discord.utils.cached_property
    def bug_channel(self):
        hook = discord.Webhook.from_url(bug_webhook, session=self.bot.session)
        return hook

    async def send_to_bugchannel(self, ctx, error, *, ping=True):
        """Sends bug to bugchannel"""

        lines = traceback.format_exception(type(error), error, error.__traceback__)
        embed = discord.Embed(title='Error', description=f"```py\n{''.join(lines)[0:4000]}\n```", color=discord.Color.red())
        embed.add_field(name='Author', value=str(ctx.author))
        embed.add_field(name='Author ID', value=str(ctx.author.id))
        embed.add_field(name='Server', value=str(ctx.guild) if ctx.guild else 'DMs')
        embed.add_field(name='Server ID', value=str(ctx.guild.id) if ctx.guild else str(ctx.author.id))
        embed.add_field(name='Channel', value=str(ctx.channel))
        embed.add_field(name='Channel ID', value=str(ctx.channel.id))
        embed.add_field(name='Command Name', value=f"```py\n {ctx.command}```")
        embed.add_field(name='Command Signature', value=f"```py\n {ctx.message.content[0:1000]}```")
        embed.add_field(name='Error in Short', value=f"```py\n{str(error)}```", inline=False)

        s = StringIO()
        s.write("".join(lines))
        s.seek(0)

        await self.bug_channel.send(embed=embed, 
                                    content="<@615785223296253953>" if ping else None, 
                                    file=discord.File(s, filename="error.txt"))

    async def post_in_bugchannel(self, ctx, error):
        """post bug in new bug forum"""

        if self.bot.is_beta:
            return

        lines = traceback.format_exception(type(error), error, error.__traceback__)
        e = "".join(lines)
        if e in self.posts:
            return

        self.posts.add(e)
        channel = self.bot.get_channel(BUG_FORUM) or await self.bot.fetch_channel(BUG_FORUM)
        embed = discord.Embed(description=f"```py\n{e[0:4000]}\n```")
        await channel.create_thread(name=f'{str(ctx.command).title()} - Error', embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog

        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return

        if isinstance(error, commands.DisabledCommand):
            return await self.error_thingy(ctx, error)

        if isinstance(error, commands.MaxConcurrencyReached):
            if str(ctx.command) == "drake":
                return
            else:
                return await self.error_thingy(ctx, error)

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                _text = f'**Wrong place,** the `{ctx.command.qualified_name}` commands can only be used in **servers** not in DMs.'
                return await self.error_thingy(ctx, _text)

            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            await self.error_thingy(
                ctx, f"You need to provide `{error.param.name.replace('_',' ')}` for this command to run."
            )

        elif isinstance(error, commands.MemberNotFound):
            _arg = error.argument
            _text = f"**Sorry,** I couldn't find any member **`{error.argument}`** in this server. Note that names are **case sensitive!**"

            if _arg.isdigit():
                _text = f"**Sorry,** I couldn't find any member with this ID **`{error.argument}`** in this server. **You have provided Invalid User ID**"

            await self.error_thingy(ctx, _text)

        elif isinstance(error, commands.UserNotFound):
            await self.error_thingy(ctx, f"**Sorry,** I couldn't find any user **`{error.argument}`** in Discord.")

        elif isinstance(error, commands.BadArgument):
            await self.error_thingy(ctx, error)

        elif isinstance(error, (commands.BotMissingPermissions, commands.MissingPermissions)):
            await self.error_thingy(ctx, error, emoji="⛔")

        elif isinstance(error, commands.BadUnionArgument):
            if error.param.name == 'user':
                ids = error.errors[0].argument
                if ids.isdigit():
                    await self.error_thingy(
                        ctx,
                        f"**Sorry,** I couldn't find any user with this ID {ids} in Discord. **You have provided Invalid ID**",
                    )
                else:
                    await self.error_thingy(ctx, f"**Sorry,** I couldn't find any user {ids} in Discord. Try using UserID.")
            else:
                await self.error_thingy(ctx, error)

        elif isinstance(error, commands.CommandOnCooldown):
            await self.error_thingy(
                ctx,
                f"{error.type.name.title()} is on cooldown, ".replace("Guild", "Server").replace("User is", "You are")
                + f"please wait `{humanize.precisedelta(timedelta(seconds=error.retry_after))}`  to use this command again",
                emoji="⏱️",
            )

        elif isinstance(error, ViewTimeoutError):
            await self.error_thingy(ctx, 'Timed Out!, I cannot wait for you longer..', emoji="⏱️")

        elif isinstance(error, ViewError):
            await self.error_thingy(ctx, f'{error}')

        elif isinstance(error, commands.NSFWChannelRequired):
            if ctx.command.qualified_name == 'reddit':
                await self.error_thingy(ctx, "This subreddit can only be used in **NSFW Channels**")

            elif ctx.command.qualified_name == 'anime':
                await self.error_thingy(ctx, "This anime is marked as NSFW. Please use this in an **NSFW Channel**")

            else:
                if ctx.author.id in {ctx.bot.owner_id, *ctx.bot.owner_ids}:
                    await ctx.reinvoke()
                else:
                    await self.error_thingy(ctx, "You can only use this command in NSFW Channels")

        elif isinstance(error, commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.Forbidden):
                await self.error_thingy(ctx, f'{original.text}')

            elif isinstance(original, discord.NotFound):
                await self.error_thingy(ctx, f'{original.text}')

            elif isinstance(original, ViewError):
                await self.error_thingy(ctx, f'{original}')

            elif isinstance(original, menus.MenuError):
                await self.error_thingy(ctx, f'{original.text}')

            elif isinstance(original, discord.HTTPException):
                await self.error_thingy(ctx, f'{original.text}')
                await self.send_to_bugchannel(ctx, error)

            elif isinstance(original, OverflowError):
                await self.error_thingy(ctx, f'{original}', emoji="<:coolredCross:731873539669360720>")
                await self.send_to_bugchannel(ctx, error, ping=False)

            else:
                await self.send_to_bugchannel(ctx, error)
                return await self.post_in_bugchannel(ctx, error)

        else:
            lines = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot.logger.error(f'Ignoring exception in command {ctx.command}:\n{lines}')
            await self.post_in_bugchannel(ctx, error)
            await self.send_to_bugchannel(ctx, error)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
