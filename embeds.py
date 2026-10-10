import discord

""" This Class is Used to standarize the Embed"""
class BotEmbed(discord.Embed):
    def __init__(self, **kwargs):
        if 'colour' not in kwargs and 'color' not in kwargs:
            kwargs['colour'] = discord.Colour.blurple()

        super().__init__(**kwargs)

        self.set_footer(text="SHiD v0.1.0-alpha.2")

class ErrorEmbed(discord.Embed):
    def __init__(self, description: str, **kwargs):
        super().__init__(
            colour=discord.Colour.red(),
            description=f"❌ {description}",
            **kwargs
        )

class InfoEmbed(discord.Embed):
    def __init__(self, description: str, **kwargs):
        super().__init__(
            colour=discord.Colour.blurple(),
            description=f"{description}",
            **kwargs
        )

class NowPlayingEmbed(discord.Embed):
    def __init__(self, description: str, link: str, **kwargs):
        super().__init__(
            title="Now Playing",
            colour=discord.Colour.blurple(),
            description=f"{description}"    
        )

        self.set_thumbnail(url=link)