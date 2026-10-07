import discord
from discord import app_commands

class NotInVoiceChannel(app_commands.CheckFailure):
    pass

class NotHavePermission(app_commands.CheckFailure):
    pass