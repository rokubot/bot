import inspect
import json

import discord
from discord.ext import commands
from pytimeparse import parse as timeparse

from .color import Color

__all__ = (
    'WholeNumber',
    'ToggleConverter',
    'EmbedDictConverter',
)

class WholeNumber(commands.Converter):
    async def convert(self, ctx, argument):
        if not argument.isdigit():
            raise commands.BadArgument("You have provided an invalid number.")
        if argument == 0:
            raise commands.BadArgument("You have to provide a number above 0")
        return int(argument)


class ToggleConverter(commands.Converter):
    async def convert(self, ctx, argument):
        lowered = argument.lower()
        if lowered in ('yes', 'y', 'true', 't', '1', 'enable', 'on'):
            return True
        elif lowered in ('no', 'n', 'false', 'f', '0', 'disable', 'off'):
            return False
        else:
            raise commands.BadArgument(
                "You have provided invalid argument. You can only use on, off, true, false as argument in this command"
            )


class EmbedDictConverter(commands.Converter):
    """Embed builder dict converter"""

    def __init__(self):
        self.content = None
        self.embed = None

    def decode_json(self, argument):
        try:
            embed = json.loads(argument)
            content = embed.pop('plainText', None)

        except (json.JSONDecodeError, TypeError):
            content = argument
            embed = None

        return content, embed

    async def convert(self, ctx, argument):
        content, embed = self.decode_json(argument)

        if embed:
            color = embed.get('color')
            image = embed.get('image')
            thumbnail = embed.get('thumbnail')

            if image and isinstance(image, str):
                image = {'url': image}
                embed['image'] = image

            if thumbnail and isinstance(thumbnail, str):
                thumbnail = {'url': thumbnail}
                embed['thumbnail'] = thumbnail

            if color and isinstance(color, str):
                try:
                    c = await Color().convert(ctx, color)
                except commands.BadArgument:
                    raise commands.BadColourArgument(color)

                embed['color'] = c.value

        self.content = content
        self.embed = embed
        return self
