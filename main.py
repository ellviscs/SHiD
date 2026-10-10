import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s')

import config

class Bot(commands.Bot):
    def __init__(self):
        intents= discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='$', intents=intents)

    async def setup_hook(self):
        if config.ENABLE_MUSIC:
            await self.load_extension('cogs.music')
            logging.info("Successfully load Music Extensions")

        try:
            if not config.ENABLE_GLOBAL:
                for GUILD_ID in config.GUILD_ID:
                    target_guild = discord.Object(id=GUILD_ID)
                    self.tree.copy_global_to(guild=target_guild)
                    synced = await self.tree.sync(guild=target_guild)
                    logging.info(f'Synced {len(synced)} commands to {str(await self.fetch_guild(target_guild.id))}')
            else:
                synced = await self.tree.sync()
                logging.info(f'Synced {len(synced)} commands to global')
        except Exception as e:
            logging.error(f'Error syncing commands: {e}')

    async def on_ready(self):
        logging.info(f'Logged on as {self.user}!')

bot = Bot()
bot.run(config.DISCORD_API_KEY, log_handler=None, reconnect=True)