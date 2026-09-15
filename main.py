import discord
from discord.ext import commands
import os
#from dotenv import load_dotenv

discord_api_key = os.getenv("DISCORD_API_KEY")
GUILD_ID = os.getenv("DISCORD_GUILD")

if not discord_api_key:
    raise ValueError("DISCORD_API_KEY not set")

if not GUILD_ID:
    raise ValueError("DISCORD_GUILD not set")

guild = discord.Object(id=int(GUILD_ID))

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='$', intents=intents)

    async def setup_hook(self):
        # Looping untuk mencari semua file .py di dalam folder cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                # Muat extension (nama folder dipisah dengan titik)
                await self.load_extension(f'cogs.{filename[:-3]}')
                print(f'Berhasil memuat cog: {filename}')

        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')

        except Exception as e:
            print(f'Error syncing commands: {e}')

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

bot = Bot()

@bot.tree.command(name="reload", description="Reload any extension and configuration")
@commands.is_owner()
async def reload_config(interaction: discord.Interaction):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            # Muat extension (nama folder dipisah dengan titik)
            await bot.reload_extension(f'cogs.{filename[:-3]}')
            print(f'Berhasil memuat cog: {filename}')

    try:
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        await interaction.response.send_message(f'Synced {len(synced)} commands to guild {guild.id}')

    except Exception as e:
        await interaction.response.send_message(f'Error syncing commands: {e}')



# @bot.command()
# async def test(ctx):
#     await ctx.send('You must enter an argument!')
# async def test(ctx, args):
#     await ctx.send(args)
#
# @bot.tree.command(name='test', description='Tests command', guild = guild)
# async def test(interaction: discord.Interaction):
#     await interaction.response.send_message('Tests command')
#
# @bot.event
# async def ban_spam(message):
#     channel = message.channel
#     if channel.name == "do-not-post":
#         member = message.author
#         await member.ban(delete_message_days=1, reason= "SPAM!")

# VIBE CODED
#     if message.content.startswith('!join'):
#         if message.author.voice:
#             channel = message.author.voice.channel
#
#             # Bot join ke channel
#             voice_client = await channel.connect()
#             await message.channel.send(f"Berhasil join ke: **{channel.name}**")
#
#             try:
#                 # Menggunakan FFmpeg untuk menangkap input audio default PC (Mikrofon)
#                 # 'audio=Microphone (...)' bisa diganti dengan nama device audio kamu
#                 FFMPEG_OPTIONS = {
#                     'executable': 'ffmpeg',  # Pastikan ffmpeg sudah di PATH
#                     'before_options': '-f dshow',
#                     'options': '-ac 2 -ar 48000'
#                 }
#
#                 device_input = 'audio=CABLE Output (VB-Audio Virtual Cable)'
#
#                 # Mulai streaming suara PC ke Discord
#                 source = discord.FFmpegPCMAudio(device_input, **FFMPEG_OPTIONS)
#                 voice_client.play(source)
#                 await message.channel.send("Sekarang menyalurkan suara dari PC ke Voice Channel...")
#
#             except Exception as e:
#                 await message.channel.send(f"Gagal memutar audio: {e}")
#         else:
#             await message.channel.send("Kamu harus masuk ke voice channel dulu!")
#
#     elif message.content.startswith('!leave'):
#         voice_client = message.guild.voice_client
#         if voice_client:
#             if voice_client.is_playing():
#                 voice_client.stop()  # Hentikan audio sebelum disconnect
#             await voice_client.disconnect()
#             await message.channel.send("Bot telah keluar dari voice channel.")
#         else:
#             await message.channel.send("Bot sedang tidak ada di voice channel mana pun.")

try:
    bot.run(discord_api_key)
except Exception as e:
    print(f"ERROR: {type(e).__name__}")
    print(f"{e}")