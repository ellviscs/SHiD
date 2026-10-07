import asyncio
import wavelink
from discord.app_commands.checks import bot_has_permissions

import checks
from errors import *
from discord.ext import commands
from embeds import *

class Music(commands.Cog):
    async def wavelink_connect(self, node):
        await self.wavelink.Pool.connect(client=self.bot, nodes=node)

    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.wavelink = bot.wavelink
        self.autoplay = True
        self.channel = None
        self.message = None
        node = [self.wavelink.Node(uri=f"http://{bot.lavalink_host}:{bot.lavalink_port}", password=bot.lavalink_password)]
        asyncio.create_task(self.wavelink_connect(node))
        print("LavaLink setup complete.")

    async def autoplay_setup(self):
        if self.autoplay:
            self.player.autoplay = wavelink.AutoPlayMode.enabled
        else:
            self.player.autoplay = wavelink.AutoPlayMode.partial

    @app_commands.command(name="autoplay", description="Autoplay the music or not")
    async def autoplay(self, interaction: discord.Interaction, autoplay : bool):
        await interaction.response.defer(ephemeral=True)
        self.autoplay = autoplay
        await self.autoplay_setup()
        await interaction.followup.send(f"The bot {"will" if autoplay else "won't"} autoplay recommended music", ephemeral=True)

    @app_commands.command(name="play", description="Play the music you want")
    @app_commands.describe(title="Song title you want to play")
    @checks.is_in_voice_channel()
    async def play(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)
        tracks: wavelink.Search = await self.wavelink.Playable.search(title, source=wavelink.TrackSource.SoundCloud)
        if not tracks:
            await interaction.followup.send(embed=ErrorEmbed(f"`{title}` not found"), ephemeral=True)
            return

        channel_target = interaction.user.voice.channel

        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            self.player: wavelink.Player= await channel_target.connect(cls=wavelink.Player)
            await self.autoplay_setup()

        self.channel = self.player.channel
        if self.channel != channel_target:
            await self.player.move_to(channel_target)

        track: wavelink.Playable = tracks[0]
        await self.player.queue.put_wait(track)

        if not self.player.playing:
            await self.player.play(self.player.queue.get())
            await interaction.followup.send(embed=InfoEmbed(f"Connected to {self.channel.name}"), ephemeral=True)
            return

        await interaction.followup.send(embed=InfoEmbed(f"Adding **{track.author} - {track.title}** to Queue"), ephemeral=True)

    @app_commands.command(name="pause", description="Pause the music")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            await interaction.followup.send("I don't play any music", ephemeral=True)
            return
        await self.player.pause(True)
        await interaction.followup.send("Pausing music", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the music")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            await interaction.followup.send("I don't play any music", ephemeral=True)
            return
        await self.player.pause(False)
        await interaction.followup.send("Resuming music", ephemeral=True)

    @app_commands.command(name="skip", description="Skip the music")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            await interaction.followup.send("I don't play any music", ephemeral=True)
            return

        await self.player.skip()
        await interaction.followup.send("Skipped", ephemeral=True)

    @app_commands.command(name="stop", description="Stop the music and disconnect the bot")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            await interaction.followup.send("Already stopped", ephemeral=True)
            return

        await self.player.disconnect()
        self.player = None
        await interaction.followup.send(f"Stopped", ephemeral=True)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        embed: discord.Embed = NowPlayingEmbed(
            f"[{payload.track.author} - {payload.track.title}]({payload.track.uri})",
            f"{payload.track.artwork}",
        )
        self.message = await self.channel.send(embed=embed, silent=True)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        await self.message.delete(delay=5)
        self.message = None

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, NotInVoiceChannel):
            embed = ErrorEmbed("You are not in a voice channel")
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

        if isinstance(error, NotHavePermission):
            embed = ErrorEmbed("You don't have permission to use this command")


async def setup(bot):
    await bot.add_cog(Music(bot))