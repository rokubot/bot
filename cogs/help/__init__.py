import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Union, List

from .help import MyNewHelp

attributes = {
    'hidden': True,
    'aliases': ['oldhelp', 'cmd', 'commands', 'command', 'category'],
    'cooldown': commands.CooldownMapping.from_cooldown(5, 5.0, commands.BucketType.user),
}


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyNewHelp(verify_checks=False, command_attrs=attributes)
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Help(bot))
