import discord


class Color:
    def __init__(self, name: str, emoji: str, color_hex: hex):
        self.name = name
        self.emoji = emoji
        self._hex = color_hex

    @property
    def color(self):
        return discord.Color(self._hex)


COLORS = Color('red', ':x:', 0xDB7BFF)
