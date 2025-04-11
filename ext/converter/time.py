from datetime import datetime, timedelta

from dateparser.search import search_dates
from discord.ext import commands
from pytimeparse import parse

__all__ = ('SimpleTimeConverter', 'HumanTime')


class SimpleTimeConverter(commands.Converter):
    """Simple time Converter that convert time to seconds"""

    async def convert(self, ctx, argument):
        time = parse(argument)
        if time is None:
            raise commands.BadArgument("You have provided invalid time format")
        return time


class HumanTime(commands.Converter):
    """A user friendly time converter."""

    def __init__(self):
        self.dt = None
        self.arg = None
        self.time = None
        self.timearg = None
        self.settings = {
            'DATE_ORDER': 'DMY',
            'TIMEZONE': 'UTC',
            'PREFER_DAY_OF_MONTH': 'first',
            'PREFER_DATES_FROM': 'future',
        }

    def __repr__(self):
        return f"<dt={self.dt} arg={self.arg} time={self.time} timearg={self.timearg}>"

    def parse_time(self, time):
        """Parse Time without quotes"""

        result = search_dates(time, settings=self.settings)
        return result

    def parse_small_time(self, time):
        """Parse small arguments like 1m, 1s"""

        seconds = parse(time)
        if seconds:
            result = datetime.now() + timedelta(seconds=seconds)
            return result

        return

    async def get_result(self, ctx, argument):
        """Running the executors in here"""

        result = await ctx.bot.loop.run_in_executor(None, self.parse_time, argument)
        if result is None:
            arg = argument.split()[0]
            dt = await ctx.bot.loop.run_in_executor(None, self.parse_small_time, arg)
            if dt:
                return [(arg, dt)]
            else:
                return None

        return result

    async def convert(self, ctx, argument):
        result = await self.get_result(ctx, argument)
        if result is None:
            self.arg = argument
            return self

        knownarg = result[0][0]
        dt = result[0][1]
        arg = argument.strip(knownarg)
        time = (dt - datetime.now()).total_seconds()

        if dt < datetime.now():
            raise commands.BadArgument("The time is in past. Please provide a valid time.")

        self.dt = dt
        self.arg = arg
        self.time = time
        self.timearg = knownarg

        return self
