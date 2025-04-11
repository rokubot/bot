from discord import Embed, ext

import config


class HelpPaginator(ext.menus.ListPageSource):
    def __init__(self, cog, commands, *, prefix):
        super().__init__(entries=commands, per_page=20)
        self.cog = cog
        self.prefix = prefix
        self.description = cog.description
        self.title = f'**{self.cog.qualified_name.title()} Commands**'

    async def format_page(self, menu, commands):
        embed = Embed(title=self.title, description=self.description, colour=config.color)
        for command in commands:
            if isinstance(command, ext.commands.Group) and command.cog.qualified_name == 'Reaction Roles':
                # hard coding RR help
                for subcmd in command.commands:
                    signature = f'**{self.prefix}{subcmd.qualified_name} {subcmd.signature}**'
                    embed.add_field(name=signature, value=subcmd.short_doc or 'No help given...', inline=False)

            elif command.cog.qualified_name == 'Reaction Roles':
                pass  # This is to avoid ro rr command

            else:
                signature = f'**{self.prefix}{command.qualified_name} {command.signature}**'
                embed.add_field(name=signature, value=command.short_doc or 'No help given...', inline=False)

        maximum = self.get_max_pages()
        if maximum > 1:
            embed.set_author(name=f'Page {menu.current_page + 1}/{maximum}')

        embed.set_footer(text=f'For more info on a command, type {self.prefix}help [command]')
        return embed
