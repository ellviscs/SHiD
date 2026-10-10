from discord import app_commands

class NotPlayingMusic(app_commands.CommandInvokeError):
    pass

class NotInSameVoiceChannel(app_commands.CheckFailure):
    pass

class NotHavePlayer(app_commands.CheckFailure):
    pass

class NotInVoiceChannel(app_commands.CheckFailure):
    pass

class NotHavePermission(app_commands.CheckFailure):
    def __init__(self, perm: str):
        self.perm = perm
        super().__init__(f"I dont have `{perm}` permission")