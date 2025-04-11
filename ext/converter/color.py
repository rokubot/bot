import inspect
import re

import discord
from discord.ext import commands

RGB_REGEX = re.compile(r'rgb\s*\((?P<r>[0-9]{1,3}%?)\s*,\s*(?P<g>[0-9]{1,3}%?)\s*,\s*(?P<b>[0-9]{1,3}%?)\s*\)')


class Color(commands.Converter):
    def parse_hex_number(self, argument):
        arg = ''.join(i * 2 for i in argument) if len(argument) == 3 else argument
        try:
            value = int(arg, base=16)
            if not (0 <= value <= 0xFFFFFF):
                raise commands.BadColourArgument(argument)
        except ValueError:
            raise commands.BadColourArgument(argument)
        else:
            return ColorSubclass(value=value)

    def parse_rgb_number(self, argument, number):
        if number[-1] == '%':
            value = int(number[:-1])
            if not (0 <= value <= 100):
                raise commands.BadColourArgument(argument)
            return round(255 * (value / 100))

        value = int(number)
        if not (0 <= value <= 255):
            raise commands.BadColourArgument(argument)
        return value

    def parse_rgb(self, argument, *, regex=RGB_REGEX):
        match = regex.match(argument)
        if match is None:
            raise commands.BadColourArgument(argument)

        red = self.parse_rgb_number(argument, match.group('r'))
        green = self.parse_rgb_number(argument, match.group('g'))
        blue = self.parse_rgb_number(argument, match.group('b'))
        return ColorSubclass.from_rgb(red, green, blue)

    async def convert(self, ctx, argument):
        if argument[0] == '#':
            return self.parse_hex_number(argument[1:])

        if argument[0:2] == '0x':
            rest = argument[2:]
            # Legacy backwards compatible syntax
            if rest.startswith('#'):
                return self.parse_hex_number(rest[1:])
            return self.parse_hex_number(rest)

        arg = argument.lower()
        if arg[0:3] == 'rgb':
            return self.parse_rgb(arg)

        arg = arg.replace(' ', '_')
        method = getattr(ColorSubclass, arg, None)
        if arg.startswith('from_') or method is None or not inspect.ismethod(method):
            raise commands.BadColourArgument(arg)
        return method()


class ColorSubclass(discord.Color):
    """Subclass of discord.COolor to add more methods"""

    @classmethod
    def default(cls):
        """A factory method that returns a :class:`Colour` with roku's default color"""
        return cls(0xDB7BFF)

    @classmethod
    def og_blurple(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x7289da``."""
        return cls(0x7289DA)

    old_blurple = og_blurple

    @classmethod
    def green(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x57f287``."""
        return cls(0x57F287)

    @classmethod
    def yellow(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xfee75c``."""
        return cls(0xFEE75C)

    @classmethod
    def fuchsia(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xeb459eE``."""
        return cls(0xEB459E)

    @classmethod
    def red(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xed4245``."""
        return cls(0xED4245)

    @classmethod
    def white(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xffffff``."""
        return cls(0xFFFFFF)

    @classmethod
    def black(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x000000``."""
        return cls(0x000000)

    @classmethod
    def blue(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0x0000FF ``."""
        return cls(0x0000FF)

    @classmethod
    def bronze(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xb8860b``."""
        return cls(0xB8860B)

    @classmethod
    def diamond(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xf8f4ec``."""
        return cls(0xF8F4EC)

    @classmethod
    def silver(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xC0C0C0``."""
        return cls(0xC0C0C0)

    @classmethod
    def gold(cls):
        """A factory method that returns a :class:`Colour` with a value of ``0xFFD700``."""
        return cls(0xFFD700)


# Monkey Patching discord.Color
discord.Color = ColorSubclass
