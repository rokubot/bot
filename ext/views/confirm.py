import discord

from .main import MainView

__all__ = 'Confirm'


class Confirm(MainView):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.value = None
        self.ctx = ctx

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.edit_message(view=self)
