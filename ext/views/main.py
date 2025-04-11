import discord

from .error import ViewTimeoutError


_all_ = ('MainView', 'SelectView')

class MainView(discord.ui.View):
    """Subclass of View with few extra functions"""

    def __init__(self, ctx, *, error_on_timeout=True):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.value = None
        self.interaction_rsp = None
        self.error_on_timeout = error_on_timeout

    def stop(self):
        for child in self.children:
            child.disabled = True
            super().stop()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                'You cannot use this menu because the command was not run by you', ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        self.stop()
        if self.interaction_rsp:
            await self.interaction_rsp.edit_message(view=self)
        if self.error_on_timeout:
            raise ViewTimeoutError('Timeout, Cannot wait for you any longer')


class SelectView(MainView):
    """Sublcass of main view with support for select"""

    def __init__(self, ctx, select):
        super().__init__(ctx)
        self.ctx = ctx
        self.value = None
        self.select = select
        self.select.callback = self.on_selecting
        self.add_item(self.select)

    async def on_selecting(self, interaction: discord.Interaction):
        self.value = self.select.values[0]
        self.stop()
        await interaction.response.edit_message(view=self)