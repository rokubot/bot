import argparse
import shlex
from typing import Generic, List, TypeVar

from discord.ext import commands

__all__ = ('add_flag', 'add_flags', 'FlagParser', 'EmptyFlagResult')

T = TypeVar('T')


class Result:
    def __init__(self):
        self._rest = None
        self._converted = []

    def __str__(self):
        return self._rest

    def __repr__(self):
        fmt = ' '.join([f'{k}={v}' for k, v in self.__dict__.items()])
        return f'<{fmt}>'


class Flag:
    def __init__(self, *args, **kwargs):
        self.names = args
        self.kwargs = kwargs

    def __repr__(self):
        args = [f'{k}={v}' for k, v in self.kwargs.items()]
        return 'Names={0} {1}'.format(self.names, *args)


def add_flag(*args, **kwargs):
    fl = Flag(*args, **kwargs)

    def inner(func):
        if isinstance(func, commands.Command):
            nfunc = func.callback
        else:
            nfunc = func

        if not hasattr(nfunc, 'flags'):
            nfunc.flags = []
        nfunc.flags.append(fl)
        return func

    return inner


def add_flags(*flags: List[Flag]):
    def inner(func):
        if isinstance(func, commands.Command):
            nfunc = func.callback
        else:
            nfunc = func

        if not hasattr(nfunc, 'flags'):
            nfunc.flags = []

        nfunc.flags = list(flags)
        return func

    return inner


class FlagParser(commands.Converter, Generic[T]):
    def __init__(self):
        self.arg_parser = argparse.ArgumentParser(exit_on_error=False, add_help=False)

    def parse(self, argument, *, namespace):
        try:
            argument = shlex.split(argument)
            parsed, rest = self.arg_parser.parse_known_args(argument, namespace=namespace)
        except Exception as error:
            raise commands.BadArgument(f'**Flag {error.argument_name}:** {error.message}')
        return parsed, rest

    async def convert(self, ctx, argument):
        flags = ctx.command.callback.flags
        for flag in flags:
            self.arg_parser.add_argument(*flag.names, **flag.kwargs)

        result = Result()
        _, unparsed = self.parse(argument, namespace=result)
        rest = ' '.join(unparsed)

        param = ctx.current_parameter
        converters = getattr(param.annotation, '__args__', None)
        if converters:
            converter = converters[0]
            converted = await commands.run_converters(ctx, converter, rest, param)
            result._converted.append(converted)
            rest = None

        result._rest = rest
        return result



class EmptyFlagResult:
    def __init__(self, *args, **kwargs):
        self.names = args
        self.kwargs = kwargs

    def __getattr__(self, name):
        return None