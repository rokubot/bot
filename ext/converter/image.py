import re

from discord.ext import commands

import config

URL_REGEX = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

__all__ = ('ImageConverter', 'ImageAttachment', 'InvalidImage', 'valid_url')


SUPPORTED_IMAGES = ('image/gif', 'image/png', 'image/webp', 'image/jpg', 'image/jpeg')


def valid_url(url: str) -> bool:
    """Checks if url is valid or not"""
    if URL_REGEX.match(url):
        return True
    return False


class InvalidImage(commands.BadArgument):
    """Exception raised when image is invalid"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ImageConverter(commands.Converter):
    """Checks if provided image link is valid and supported"""

    def __init__(self, check_url: bool = True):
        self.check_url = check_url

    async def convert(self, ctx, argument) -> str:
        if self.check_url and not valid_url(argument):
            raise InvalidImage('You have provided **invalid image Link**')

        r = await ctx.bot.session.get(argument)
        if argument.startswith('https://images.app.goo.gl'):
            argument = str(r.url).split('imgurl=')[1].split('&imgrefurl')[0]

        if r.status == 200 and r.headers['Content-Type'] in SUPPORTED_IMAGES:
            return argument

        raise InvalidImage("You have provided **invalid image link**")


def get_attachment(ctx: commands.Context):
    attachments = ctx.message.attachments[0]
    if len(attachments) > 0:
        return attachments[0].url


ImageAttachment = commands.parameter(default=get_attachment, displayed_default='<attachment>', converter=ImageConverter)
