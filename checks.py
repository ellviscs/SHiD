import discord
from discord import app_commands
import errors


def is_in_voice_channel():
    def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or not interaction.user.voice.channel: raise errors.NotInVoiceChannel()
        return True
    return app_commands.check(predicate)