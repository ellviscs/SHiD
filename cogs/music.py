import asyncio
import discord
import wavelink
from discord import app_commands
from discord.ext import commands


class Music(commands.Cog):
    async def wavelink_connect(self, node):
        await self.wavelink.Pool.connect(client=self.bot, nodes=node)

    def __init__(self, bot):
        self.bot = bot
        self.player = None
        self.wavelink = bot.wavelink
        self.autoplay = True
        self.channel = None
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
    async def play(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer(ephemeral=True)
        tracks: wavelink.Search = await self.wavelink.Playable.search(title)
        if not tracks:
            interaction.followup.send(f"No tracks found for that {title}", ephemeral=True)
            return

        self.channel = interaction.user.voice.channel
        if not self.channel:
            interaction.followup.send("You must join a voice channel first", ephemeral=True)

        self.player: wavelink.Player = interaction.guild.voice_client
        if not self.player:
            self.player: wavelink.Player= await self.channel.connect(cls=wavelink.Player)
            await self.autoplay_setup()

        track: wavelink.Playable = tracks[0]
        await self.player.queue.put_wait(track)

        if not self.player.playing:
            await self.player.play(self.player.queue.get())
            await interaction.followup.send(f"Playing **{track.author} - {track.title}**", ephemeral=True)
            return

        await interaction.followup.send(f"Adding **{track.author} - {track.title}** to Queue", ephemeral=True)

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

        await self.player.stop()
        await self.player.disconnect()
        self.player = None
        await interaction.followup.send(f"Stopped", ephemeral=True)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        embed: discord.Embed = discord.Embed(
            title="Now Playing",
            colour=discord.Colour.blue(),
            description=f"[{payload.track.author} - {payload.track.title}]({payload.track.uri})",
        )
        await self.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))