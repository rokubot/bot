import re

import discord
import humanize
from discord.ext import menus

from config import color

__all__ = (
    'EmbedPaginator',
    'LevelPages',
    'TodoPages',
    'WarnPages',
    'WelcomeFontPages',
    'WelcomeImagePages',
    'GooglePages',
    'AnimePages',
    'WikiPages',
    'UrbanDictionaryPageSource',
)


class TablePages(menus.ListPageSource):
    """Table Paginator"""

    def __init__(self, entries, *, per_page=1):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu, page):
        return  f"```js\n{page}```"
    


class EmbedPaginator(menus.ListPageSource):
    """An Overall Embed Paginator"""

    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, embed):
        return embed


class LevelPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=8)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = discord.Embed(
            title="Server Level Leaderboard",
            color=color,
            description='\n'.join(f'{i}. {v}' for i, v in enumerate(entries, offset)),
        )
        return embed


class TodoPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = discord.Embed(
            title="Todo List", color=color, description='\n'.join(f'`[{i}]` {v}' for i, v in enumerate(entries, offset))
        )
        return embed


class WarnPages(menus.ListPageSource):
    def __init__(self, title, footer, data):
        self.em_title = title
        self.em_footer = footer
        super().__init__(data, per_page=5)

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page + 1
        embed = discord.Embed(
            title=self.em_title, color=color, description='\n'.join(f'**{i}. ** {v}' for i, v in enumerate(entries, offset))
        )
        embed.set_footer(text=self.em_footer)

        return embed


class WelcomeFontPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, fontdata):
        embed = discord.Embed(
            color=color,
            title=f"Font Image List [{menu.current_page + 1} / {self.get_max_pages()}]",
            description=f"**Font Name: ** {fontdata['name']}\n"
            f"**Default Size: ** {fontdata['size']}\n"
            f"**Default Spacing: {fontdata['spacing']}**\n",
        )
        embed.set_image(url=fontdata['image'])

        return embed


class WelcomeImagePages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    # abdullah
    async def format_page(self, menu, entries):
        d = 'White (default)'
        embed = discord.Embed(
            color=color,
            title=f"Images List [{menu.current_page + 1} / {self.get_max_pages()}]",
            description=f"**__Textcolor :__**  **{entries.get('textcolor',d)}**\n",
        )

        embed.description += (
            f"**__Textborder :__** **{entries.get('textborder', 'Black (default)')}**"
            f"\n**__Avatarborder :__**  **{entries.get('avatarborder', d)}**"
            f"\n**__EDITMODE :__** **{'ON' if entries.get('shouldedit', False)  else 'OFF'} **"
        )

        embed.set_image(url=entries['image'])

        return embed


class GooglePages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, resp):
        embed = discord.Embed(title=resp.title, description=resp.description[0:2040], color=color, url=resp.url)
        embed.set_thumbnail(url=resp.image_url if resp.image_url.startswith('http') else "")
        return embed


class Snipe(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, results1):
        embed = discord.Embed(description=f"{results1['message_content']}", color=color)
        embed.set_author(name=f"{results1['author']}", icon_url=f"{results1['author'].avatar_url}")
        embed.set_footer(
            text=f"Deleted {humanize.naturaltime(results1['timestamp'])} | Page {menu.current_page + 1} of {self.get_max_pages()}"
        )
        embed.set_image(url=results1.get('message_image', ''))
        return embed


class AnimePages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, resp):
        title_en = resp['attributes']['titles'].get('en')
        title_en_jp = resp['attributes']['titles'].get('en_jp')
        title_ja_jp = resp['attributes']['titles'].get('ja_jp')
        title = title_en_jp or title_en or title_ja_jp

        embed = discord.Embed(title=title, color=color)
        embed.description = f"**__Description:__** \n{resp['attributes']['description']}"
        embed.add_field(name="__Type:__", value=resp['attributes']['showType'])
        embed.add_field(name="__Episodes:__", value=resp['attributes']['episodeCount'])
        embed.add_field(name="__Status:__", value=resp['attributes']['status'].replace("current", "ongoing").title())
        embed.add_field(name="__Aired On:__", value=resp['attributes']['startDate'])
        embed.add_field(name="__Popularity:__", value=resp['attributes']['popularityRank'])
        embed.add_field(name="__Ranking:__", value=resp['attributes']['ratingRank'])
        embed.add_field(name="__Average Rating:__", value=resp['attributes']['averageRating'])
        embed.add_field(name="__Age Rating:__", value=resp['attributes']['ageRatingGuide'] or "Not specified")
        embed.add_field(name="__NSFW:__", value=resp['attributes']['nsfw'])
        a = title_en or '\u200b'
        b = title_ja_jp or '\u200b'
        embed.add_field(name="__Alternative Titles:__", value=f"{a} \n{b}", inline=False)
        embed.set_thumbnail(url=resp['attributes']['posterImage']['original'])
        return embed


class WikiPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1)

    async def format_page(self, menu, resp):
        s = await resp.summary()
        if len(s) >= 2048:
            s = s[0:2040] + '...'
        embed = discord.Embed(description=s, colour=color)
        embed.set_author(name="Wikipedia", icon_url="https://i.imgur.com/RSwCcOj.png")
        return embed


class UrbanDictionaryPageSource(menus.ListPageSource):
    BRACKETED = re.compile(r'(\[(.+?)\])')

    def __init__(self, data):
        super().__init__(entries=data, per_page=1)

    def cleanup_definition(self, definition, *, regex=BRACKETED):
        def repl(m):
            word = m.group(2)
            return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

        ret = regex.sub(repl, definition)
        if len(ret) >= 2048:
            return ret[0:2000] + ' [...]'
        return ret

    async def format_page(self, menu, entry):
        maximum = self.get_max_pages()
        title = f'{entry["word"]}: {menu.current_page + 1} out of {maximum}' if maximum else entry['word']
        embed = discord.Embed(title=title, colour=color, url=entry['permalink'])
        embed.set_footer(text=f'by {entry["author"]}')
        embed.description = self.cleanup_definition(entry['definition'])

        try:
            up, down = entry['thumbs_up'], entry['thumbs_down']
        except KeyError:
            pass
        else:
            embed.add_field(name='Votes', value=f'\N{THUMBS UP SIGN} {up} \N{THUMBS DOWN SIGN} {down}', inline=False)

        try:
            date = discord.utils.parse_time(entry['written_on'][0:-1])
        except (ValueError, KeyError):
            pass
        else:
            embed.timestamp = date

        return embed
