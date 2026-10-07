import discord
from discord import app_commands
from discord.ext.commands import bot_has_permissions

import errors


def is_in_voice_channel():
    def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or not interaction.user.voice.channel: raise errors.NotInVoiceChannel()
        return True
    return app_commands.check(predicate)

def have_permission_for_music():
    def predicate(interaction: discord.Interaction) -> bool:
        target_channel = interaction.user.voice.channel
        if interaction.user.voice.channel.permissions_for(interaction.guild.me).connect: return True
        raise errors.NotHavePermission("connect")
    return app_commands.check(predicate)