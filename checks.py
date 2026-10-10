import discord
from discord import app_commands
import errors

def has_voice_client():
    def predicate(interaction: discord.Interaction) -> bool:
        player = interaction.guild.voice_client
        if not player: raise errors.NotHavePlayer()
        return True
    return app_commands.check(predicate)

def has_permissions_to(permission: Union[str, List[str]]):
    if isinstance(permission, str):
        permission = [permission]

    def predicate(interaction: discord.Interaction) -> bool:
        target_channel = interaction.user.voice.channel
        permissions = target_channel.permissions_for(interaction.guild.me)

        for perm in permission:
            if not hasattr(permissions, perm) or not getattr(permissions, perm):
                raise errors.NotHavePermission(perm)
        return True
    return app_commands.check(predicate)

def is_in_voice_channel(same_channel: bool = False):
    def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise errors.NotInVoiceChannel()

        if same_channel:
            player = interaction.guild.voice_client
            if player.channel != interaction.user.voice.channel:
                raise errors.NotInSameVoiceChannel()

        return True

    return app_commands.check(predicate)

def have_permission_for_music():
    def predicate(interaction: discord.Interaction) -> bool:
        target_channel = interaction.user.voice.channel
        if interaction.user.voice.channel.permissions_for(interaction.guild.me).connect: return True
        raise errors.NotHavePermission("connect")
    return app_commands.check(predicate)