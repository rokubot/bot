import asyncio
import logging
import os
import re
import gettext
from collections import Counter
from datetime import datetime, timezone
from typing import Coroutine, Optional, Union

import aiohttp
import discord
import motor.motor_asyncio
import uvloop
from discord.ext import commands

import config
import ext


os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

_ = ext.i18n._

async def _get_prefix(bot, message):
    user_id = bot.user.id
    base = [f'<@!{user_id}>', f'<@{user_id}>']
    common_prefix = bot.common_prefix.copy()

    if not message.guild:
        base.extend(common_prefix)
        base.append('')

    else:
        try:
            _pre = bot.prefixes[message.guild.id]
        except KeyError:
            _pre = common_prefix
        finally:
            base.extend(_pre)  # type: ignore

    base = sorted(base, key=len, reverse=True)
    for prefix in base:
        match = re.match(rf"^({re.escape(prefix)}\s*).*", message.content, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    return base


logger = ext.log.create_logger(level=logging.INFO)


class RokuBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=_get_prefix,
            case_insensitive=True,
            intents=discord.Intents.all(),
            activity=discord.Game("Ro help"),
            owner_id=615785223296253953,
            chunk_guilds_at_startup=False,
        )
        self.loop = asyncio.get_running_loop()
        self._ready = asyncio.Event()
        self.logger = logger
        self.warn_prompt = ext.views.Confirm
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.real_db = motor.motor_asyncio.AsyncIOMotorClient(config.DB_URL)
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()
        self.prefixes = {}
        self.banned_users = {}
        self.command_checks = {}
        self.premium_users = {}
        self.premium_guilds = []

        self._user_lang = {} # {id: lang}
        self._guild_lang = {} # {id: lang}

        self.spam_control = commands.CooldownMapping.from_cooldown(12, 12.0, commands.BucketType.user)
        self._auto_spam_count = Counter()
        self.add_check(self.disabled_check)

    @property
    def db(self):
        return self.real_db.roku

    @property
    def is_beta(self):
        return os.getenv('BETA', False)

    @property
    def common_prefix(self):
        common_prefix = ['Roku', 'Ro']
        if self.is_beta:
            common_prefix = ['$$$$']

        return common_prefix
    
    def get_lang(self, user_id: int, guild_id: int = None):
        if guild_id and self._guild_lang.get(guild_id):
            return self._guild_lang.get(guild_id)
        return self._user_lang.get(user_id, 'en_US')

    async def on_ready(self):
        if not hasattr(self, 'launch_time'):
            self.launch_time = datetime.now(tz=None)

        if hasattr(self, 'cluster'):
            logger.info(f'Logged in as {self.user}')
            logger.info(f'Cluster {self.cluster.id}: {self.shard_ids}')  # type: ignore
        else:
            logger.info(f'Logged in as {self.user}')

    @discord.utils.cached_property
    def webhook(self):
        hook = discord.Webhook.from_url(config.webhook_url, session=self.session)
        return hook

    async def getch_user(self, user_id, *, guild: Optional[discord.Guild] = None):
        """|coro|
        Tries to find user from cache, fallbacks to API callback
        Parameters
        -----------
        user_id: int
        guild: Optional[:class: `discord.Guild`]


        Returns
        --------
        Optional[Union[:class:`discord.Member`, :class:`discord.User`]
            The User or ``None`` if not found.
        """
        if guild:
            user = guild.get_member(user_id)
            if user is None:
                try:
                    user = await guild.fetch_member(user_id)
                except discord.NotFound:
                    pass
                else:
                    return user
            else:
                return user
        else:
            user = self.get_user(user_id)

        if user is None:
            try:
                user = await self.fetch_user(user_id)
            except discord.NotFound:
                return

        return user

    async def setup_hook(self) -> None:
        if self.is_beta:
            guild = discord.Object(id=697029214289002536, type=discord.Guild)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    async def disabled_check(self, ctx):
        if ctx.guild is None:
            return True

        _dict = self.command_checks.get(ctx.guild.id)
        if _dict is None:
            _dict = await self.db.enabler.find_one(ctx.guild.id) or {}
            self.command_checks[ctx.guild.id] = _dict

        cmd_check = _dict.get(ctx.command.qualified_name.title(), True)
        if not cmd_check:
            raise commands.DisabledCommand(
                _("{command} command is disabled in this server. ").format(command=ctx.command.qualified_name.title())
                + _("Type `{prefix}enable {command}` to enable this command").format(
                    prefix=ctx.prefix, command=ctx.command.qualified_name
                )
            )

        if ctx.cog:
            cog_check = _dict.get(ctx.cog.qualified_name.title(), True)
            if not cog_check:
                raise commands.BadArgument(
                    _("{category} category is disabled in this server. ").format(category=ctx.cog.qualified_name)
                    + _("Type `{prefix}enable {category}` to enable this command ").format(
                        prefix=ctx.prefix, category=ctx.command.qualified_name
                    )
                )

        return True

    async def process_commands(self, message: discord.Message) -> Optional[discord.Message]:  # type: ignore
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.command is None:
            return
        
        lang = self.get_lang(ctx.author.id, ctx.guild.id)
        ext.i18n.i18n.set_lang(lang)

        await self.invoke(ctx)

    async def close(self):
        await super().close()
        await self.session.close()
        self.real_db.close()


async def main():
    bot = RokuBot()
    async with bot:
        for extension in config.initial_extensions:
            await bot.load_extension(extension)
        await bot.start(config.TOKEN, reconnect=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
