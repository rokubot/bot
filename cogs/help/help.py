import difflib
import inspect
from typing import Any, List, Mapping, Optional

import discord
from discord.ext import commands

from config import color
from ext.views import MainView, ViewMenuPages
from ext.i18n import _

from .paginator import HelpPaginator

LINKS = {
    'Invite Roku': 'https://rokubot.com',
    'Support Server': 'https://discord.gg/pkn6TzW',
    'Vote': 'https://top.gg/bot/706531890718310492/vote',
    'Website': 'https://rokubot.com',
    'Donate': 'https://ko-fi.com/rokubot',
    'Membership': 'https://ko-fi.com/rokubot/tiers',
    'Privacy Policy': 'https://rokubot.com/privacy',
    'ToS': 'https://rokubot.com/terms',
}

LINKS_FMT = [f"**[{name}]({url})**" for name, url in LINKS.items()]


class MyNewHelp(commands.HelpCommand):
    def get_opening_note(self):
        command_name = self.invoked_with
        text = """Prefix of this bot is `{0}`
        Use `{0}{1} [command | category]` for more info on a command or a category.

        Do not include `<>`, `[ ]` 
        `<>` means required argument.
        `[ ]` means optional argument.
        """.format(
            self.clean_prefix, command_name
        )

        return inspect.cleandoc(text)

    def get_command_signature(self, command: commands.Command):
        return '`%s%s %s`' % (self.clean_prefix, command.qualified_name, command.signature)
    
    def help_template(self, text):
        """Replaces prefix and few things, also localizes the text"""

        ctx = self.context
        text = _(text) or _('No description provided.')
        to_replace = {
            '{.prefix}': ctx.clean_prefix,
            '{.user}': str(ctx.author),
            '{.username}': ctx.author.name,
            '{.mention}': str(ctx.author.mention),
            '{.id}': str(ctx.author.id),
            '{.guild}': str(ctx.guild),
        }

        for i, k in to_replace.items():
            text = text.replace(i, k)

        return text

    def command_not_found(self, string: str):
        match = difflib.get_close_matches(
            string, [c for c in self.context.bot.all_commands if not self.context.bot.get_command(c).hidden]  # type: ignore
        )

        if len(match) == 0:
            return f'No command called `{string}` found.'

        return 'No command called `{}` found.\n**Did you mean?**  `\n{}`'.format(string, '\n'.join(match))

    def subcommand_not_found(self, command: commands.Command, string: str):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            match = difflib.get_close_matches(string, [c.name for c in command.commands if not c.hidden])

            if len(match) == 0:
                return 'Command "{0.qualified_name}" has no subcommand named {1}'.format(command, string)

            return 'Command `{0.qualified_name}` has no subcommand named {1}..\n**Did you mean?** \n`{2}`'.format(
                command, string, f'\n'.join([f"{command.qualified_name} {m}" for m in match])
            )

        return f'Command `{command}` has no subcommands.'

    async def send_old_command_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]]):
        embed = discord.Embed(title='Roku Command List', colour=color)
        embed.description = self.get_opening_note()

        for cog, cmds in mapping.items():
            name = 'No Category' if cog is None else f"__{cog.qualified_name.title()}__"
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                value = '\u2002 '.join(f"`{c.name}`" for c in cmds if not c.hidden)
                if cog and cog.description:
                    value = '\n{0}'.format(value)

                embed.add_field(name=name, value=value, inline=False)

        fmt = ' '.join([' | '.join(LINKS_FMT[:-1]), LINKS_FMT[-1]])
        embed.add_field(name="Extra links", value=fmt, inline=False)

        await self.get_destination().send(embed=embed)  # type: ignore

    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], List[commands.Command[Any, ..., Any]]]) -> None:
        if self.context.invoked_with in ('cmd', 'command', 'commands'):
            return await self.send_old_command_help(mapping)

        embed = discord.Embed(title='Help Menu', colour=color)
        embed.description = self.get_opening_note()
        embed.set_image(url='https://i.imgur.com/msBBOXt.gif')
        options = []

        for cog, commands in mapping.items():
            if cog is None:
                continue

            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                emoji = getattr(cog, 'emoji', ':x:')
                name = cog.qualified_name.title()
                name_fmt = f"**{emoji} {name}**"

                description = cog.description[:95] or "No description"
                help_txt = getattr(cog, "help_txt", cog.qualified_name.lower())
                value = f'`{self.clean_prefix}help {help_txt} `\n{cog.description}\n'

                embed.add_field(name=name_fmt, value=value)
                option = discord.SelectOption(label=name, description=description, emoji=emoji)
                options.append(option)

        fmt = ' '.join([' | '.join(LINKS_FMT[:-1]), LINKS_FMT[-1]])
        embed.add_field(name="Extra links", value=fmt, inline=False)

        select = discord.ui.Select(placeholder='Select from categories', options=options)
        buttons = [discord.ui.Button(label=name, url=url) for name, url in LINKS.items()]

        async def select_callback(interaction: discord.Interaction):
            ctx = self.context
            ctx.interaction = interaction  # type: ignore
            if interaction.user.id not in {ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}:  # type: ignore
                return await interaction.response.send_message(
                    'You cannot use this menu because this command was not started by you ', ephemeral=True
                )
            await interaction.response.defer()
            cog = ctx.bot.get_cog(select.values[0])
            await self.send_cog_help(cog)  # type: ignore

        select.callback = select_callback

        view = MainView(self.context, error_on_timeout=False)
        view.add_item(select)
        for button in buttons:
            view.add_item(button)

        await self.get_destination().send(embed=embed, view=view)

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)

        options = []
        for command in filtered:
            name = command.qualified_name.title()
            description = self.help_template(command.help)[:95]
            option = discord.SelectOption(label=name, description=description)
            options.append(option)

        select = discord.ui.Select(placeholder='Select from commands', options=options)

        async def select_callback(interaction):
            ctx = self.context
            ctx.interaction = interaction
            if interaction.user.id not in {ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}:  # type: ignore
                return await interaction.response.send_message(
                    'You cannot use this menu because this command was not started by you ', ephemeral=True
                )
            await interaction.response.defer()
            command = ctx.bot.get_command(select.values[0])
            if isinstance(command, commands.Group):
                await self.send_group_help(command)
            else:
                await self.send_command_help(command)

        select.callback = select_callback

        menu = ViewMenuPages(
            HelpPaginator(cog, filtered, prefix=self.clean_prefix), clear_reactions_after=True, items=[select]
        )

        await menu.start(self.context)


    async def send_group_help(self, group):
        """Help for each Group"""

        embed = discord.Embed(title=f"Help for {group.qualified_name} Commands", colour=color)
        embed.add_field(name="__Usage:__", value=f"{self.get_command_signature(group)}")
        embed.add_field(name="__Aliases:__", value="\u2002 ".join(f"`{alias}`" for alias in group.aliases) or "`None`")
        if group.help:
            embed.add_field(name="__Description:__", value=group.help or "\u2002", inline=False)

        options = []

        if isinstance(group, commands.Group):
            string = ""
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                string += f"{self.get_command_signature(command)} - {command.short_doc or 'No Description'} \n\n"
                name = command.qualified_name.title()
                description = self.help_template(command.short_doc)[:95]
                option = discord.SelectOption(label=name, description=description)
                options.append(option)

            embed.add_field(name="__Subcommands:__", value=string, inline=False)

        embed.set_image(url=f"https://rokubot.com/images/cmd/{group.qualified_name.replace(' ', '-')}.gif")
        embed.set_footer(text=f"For more info on a command, type {self.clean_prefix}help [command]")
        select = discord.ui.Select(placeholder='Select from commands', options=options)

        async def select_callback(interaction):
            ctx = self.context
            ctx.interaction = interaction
            if interaction.user.id not in {ctx.bot.owner_id, ctx.author.id, *ctx.bot.owner_ids}:  # type: ignore
                return await interaction.response.send_message(
                    'You cannot use this menu because this command was not started by you ', ephemeral=True
                )
            await interaction.response.defer()
            command = ctx.bot.get_command(select.values[0])
            await self.send_command_help(command)

        select.callback = select_callback

        view = MainView(self.context, error_on_timeout=False)
        view.add_item(select)

        await self.get_destination().send(embed=embed, view=view)

    async def send_command_help(self, command: commands.Command):
        """Help for Each Command"""

        signature = self.get_command_signature(command)
        embed = discord.Embed(color=color, title=f"**Help for `{self.clean_prefix}{command}` command**")
        embed.add_field(name="Usage", value=f"{signature}")
        embed.add_field(name="Aliases", value="\u2002 ".join(f"`{alias}`" for alias in command.aliases) or "`None`")
        embed.add_field(name="Description", value=self.help_template((command.help)), inline=False)

        cmd_data = command.__original_kwargs__

        keyword = cmd_data.get('keyword')
        if keyword:
            embed.add_field(
                name=f"Keywords (Variables) that can be used in {command}", value=self.help_template(keyword), inline=False
            )

        flags = cmd_data.get('flag')
        if flags:
            embed.add_field(name="Flags", value=self.help_template(flags), inline=False)

        examples = cmd_data.get('examples')
        if examples:
            embed.add_field(name="Examples", value=examples, inline=False)

        embed.set_image(url=f"https://rokubot.com/images/cmd/{command.qualified_name.replace(' ', '-')}.gif")
        embed.set_footer(text=f"For more help, join support server!")
        await self.get_destination().send(embed=embed)
