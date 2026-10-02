import discord
from discord.ext import commands
import wavelink
import os

DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")
GUILD_ID = os.getenv("DISCORD_GUILD")

if not DISCORD_API_KEY:
    raise ValueError("DISCORD_API_KEY not set")

if not GUILD_ID:
    raise ValueError("DISCORD_GUILD not set")

guild = discord.Object(id=int(GUILD_ID))

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='$', intents=intents)
        self.guild = None
        self.wavelink = wavelink
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_global_instruction = os.getenv("GEMINI_GLOBAL_INSTRUCTION")
        self.lavalink_host = os.getenv("LAVALINK_HOST")
        self.lavalink_port = os.getenv("LAVALINK_PORT")
        self.lavalink_password = os.getenv("LAVALINK_PASSWORD")
        self.guild_chat_id = int(os.getenv("GUILD_CHAT_ID"))

    async def setup_hook(self):
        self.guild = await self.fetch_guild(guild.id)
        if self.lavalink_port and self.lavalink_host:
            await self.load_extension('cogs.music')
            print("Successfully load Music Extensions")
        if self.gemini_api_key:
            await self.load_extension('cogs.chatbot')
            print("Successfully load Chatbot Extensions")
        await self.load_extension('cogs.general')
        print("Successfully load General Extensions")

        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to {str(self.guild)}')

        except Exception as e:
            print(f'Error syncing commands: {e}')

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

bot = Bot()

try:
    bot.run(DISCORD_API_KEY)
except Exception as e:
    print(f"ERROR: {type(e).__name__}")
    print(f"{e}")