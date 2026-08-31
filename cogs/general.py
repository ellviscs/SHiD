import discord
from discord.ext import commands
from discord import app_commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        channel = message.channel
        if message.content == "hello" or message.content == "hi":
            await channel.send(f'Hello {message.author}!')

        if channel.name == "do-not-post":
            member = message.author
            await member.ban(delete_message_days=1, reason= "SPAM!")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Welcome {member.mention}!')

    @app_commands.command(name="ping", description="Ping")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    @app_commands.command(name="hello", description="Hello")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(General(bot))