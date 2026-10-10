import asyncio
from email import message

import discord
import wavelink
from google.genai._gaos.utils import unions
from wavelink import tracks

import checks
import config
import errors
from discord import app_commands, channel
from discord.ext import commands
import embeds
import logging

logger = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message = {}
        self.autoplay = {}

    async def cog_load(self):
        asyncio.create_task(self.connect_lavalink())

    async def connect_lavalink(self):
        node = [wavelink.Node(
            uri=f"http://{config.LAVALINK_HOST}:{config.LAVALINK_PORT}",
            password=config.LAVALINK_PASS
        )]
        await wavelink.Pool.connect(client=self.bot, nodes=node)
        logger.info("LavaLink setup complete.")

    async def change_channel_status(self, object, clear: bool = False, paused: bool = False):
        if isinstance(object, discord.Interaction):
            player = object.guild.voice_client
        else:
            player = object.player

        channel = player.channel
        me = channel.guild.me
        permissions = channel.permissions_for(me)

        if not permissions.manage_channels:
            return

        if clear:
            await channel.edit(status=None)
            return

        track = player.current

        if paused:
            await channel.edit(status=f":pause_button: {track.author} - {track.title}")
            return

        await channel.edit(status=f":arrow_forward: {track.author} - {track.title}")

    async def autoplay_setup(self, interaction: discord.Interaction):
        guild = interaction.guild
        player = guild.voice_client

        if not guild.id in self.autoplay:
            self.autoplay[guild.id] = True

        if self.autoplay.get(guild.id):
            player.autoplay = wavelink.AutoPlayMode.enabled
        else:
            player.autoplay = wavelink.AutoPlayMode.partial

    @app_commands.command(name="autoplay", description="Autoplay the music or not")
    async def autoplay(self, interaction: discord.Interaction, autoplay : bool):
        await interaction.response.defer(ephemeral=True)
        self.autoplay[interaction.guild.id] = autoplay
        await self.autoplay_setup(interaction)
        await interaction.followup.send(f"The bot {"will" if autoplay else "won't"} play recommended music", ephemeral=True)

    @app_commands.command(name="play", description="Play the music you want")
    @app_commands.describe(title="Song title you want to play")
    @checks.has_permissions_to(["connect","speak"])
    @checks.is_in_voice_channel()
    async def play(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)
        tracks: wavelink.Search = await wavelink.Playable.search(title, source=wavelink.TrackSource.YouTubeMusic)
        if not tracks:
            await interaction.followup.send(embed=embeds.ErrorEmbed(f"`{title}` not found"), ephemeral=True)
            return

        channel_target = interaction.user.voice.channel

        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            player: wavelink.Player= await channel_target.connect(cls=wavelink.Player)
            await self.autoplay_setup(interaction)

        channel = player.channel
        if channel != channel_target:
            await player.move_to(channel_target)

        track: wavelink.Playable = tracks[0]
        await player.queue.put_wait(track)

        if not player.playing:
            await player.play(player.queue.get())
            await interaction.followup.send(embed=embeds.InfoEmbed(f"Connected to {channel.name}"), ephemeral=True)
            return

        await interaction.followup.send(embed=embeds.InfoEmbed(f"**{track.author} - {track.title}** was added"), ephemeral=True)

    @app_commands.command(name="pause", description="Pause the music")
    @checks.is_in_voice_channel(same_channel=True)
    @checks.has_voice_client()
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        player: wavelink.Player = interaction.guild.voice_client

        if player.paused:
            await interaction.followup.send(
                embed=embeds.ErrorEmbed("The Player already paused")
            )
            return

        await player.pause(True)
        await self.change_channel_status(interaction,paused=True)
        await interaction.followup.send(
            embed=embeds.InfoEmbed("Pausing music"),
            ephemeral=True
        )

    @app_commands.command(name="resume", description="Resume the music")
    @checks.is_in_voice_channel(same_channel=True)
    @checks.has_voice_client()
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client

        if not player.paused:
            await interaction.followup.send(
                embed=embeds.ErrorEmbed("The Player already resumed")
            )
            return

        await player.pause(False)
        await self.change_channel_status(interaction)
        await interaction.followup.send(
            embed=embeds.InfoEmbed("The player has been resumed"),
            ephemeral=True
        )

    @app_commands.command(name="skip", description="Skip the music")
    @checks.is_in_voice_channel(same_channel=True)
    @checks.has_voice_client()
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client

        track = await player.skip()
        if not track:
            raise errors.NotPlayingMusic

        await interaction.followup.send(
            embed=embeds.InfoEmbed(f"{track.title} was skipped!"),
            ephemeral=True
        )

    @app_commands.command(name="stop", description="Stop the music and disconnect the bot")
    @checks.is_in_voice_channel(same_channel=True)
    @checks.has_voice_client()
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client

        await player.disconnect(force=True)

        if self.message[player.guild.id]:
            message = self.message.pop(player.guild.id)
            message.delete()

        await interaction.followup.send(
            embed=embeds.InfoEmbed("The music has been stop.")
        )

    @app_commands.command(name="volume", description="Clear the music")
    @checks.is_in_voice_channel(same_channel=True)
    @checks.has_voice_client()
    async def volume(self, interaction: discord.Interaction, volume: app_commands.Range[int, 1, 200]):
        await interaction.response.defer(ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client

        await player.set_volume(volume)
        await interaction.followup.send(
            embed = embeds.InfoEmbed(f"The volume has set to: {volume} by {interaction.user.name}")
        )

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        guild = payload.player.guild
        channel = payload.player.channel
        if not guild.id in self.message:
            self.message[guild.id] = None

        await self.change_channel_status(payload)

        self.message[guild.id] = await channel.send(
            embed=embeds.NowPlayingEmbed(
                f"[{payload.track.author} - {payload.track.title}]({payload.track.uri})",
                f"{payload.track.artwork}"
            ),
            silent=True
        )

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        await self.change_channel_status(payload, clear=True)

        guild = payload.player.guild
        message = self.message[guild.id]
        if message is not None:
            try:
                await message.delete(delay=1)
            except discord.NotFound:
                pass


    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, errors.NotInSameVoiceChannel):
            await interaction.response.send_message(
                embed=embeds.ErrorEmbed("Not in the same voice channel!"),
                ephemeral=True,
            )
            return

        if isinstance(error, errors.NotHavePlayer) or isinstance(error, errors.NotPlayingMusic):
            await interaction.followup.send(
                embed=embeds.ErrorEmbed("I don't play any music!"),
                ephemeral=True
            )
            return

        if isinstance(error, errors.NotInVoiceChannel):
            await interaction.response.send_message(
                embed=embeds.ErrorEmbed("You are not in a voice channel!"),
                ephemeral=True,
            )
            return

        if isinstance(error, errors.NotHavePermission):
            missing_permission = error.perm
            await interaction.response.send_message(
                embed=embeds.ErrorEmbed(f"I dont have `{missing_permission}` permission"),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=embeds.ErrorEmbed("An error has occurred, please try again!"),
        )

async def setup(bot):
    await bot.add_cog(Music(bot))