import discord
import nacl
import davey
import yt_dlp
import asyncio
import re
from discord.ext import commands
from discord import app_commands

# Konfigurasi yt-dlp
# default_search='auto' akan otomatis melakukan 'ytsearch:' jika input bukan sebuah URL valid
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'default_search': 'auto',
    'quiet': True,
    'no_warnings': True,
}

# Konfigurasi FFmpeg
# Opsi reconnect ini sangat penting agar audio tidak terputus jika ada gangguan koneksi sementara
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn', # -vn berarti tidak perlu memproses video, hanya audio
}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    def sanitize_input(self, query: str) -> str:
        """
        Membersihkan input pengguna dari karakter berbahaya.
        Hanya mengizinkan huruf, angka, spasi, dan karakter yang umum ada pada URL.
        """
        # Menghapus spasi berlebih di awal/akhir
        query = query.strip()
        # Batasi panjang input agar tidak membebani memori/parser
        query = query[:200]
        # Regex untuk mengizinkan alfanumerik, spasi, dan karakter URL dasar (-, ., :, /, ?, =, &, _)
        sanitized = re.sub(r'[^\w\s\-\.\:\/\?\=\&]', '', query)
        if '.' in sanitized:
            return sanitized
        return sanitized + "audio"

    @app_commands.command(name="join", description="Join to voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "Kamu harus bergabung ke voice channel terlebih dahulu!",
                ephemeral=True  # Pesan error hanya dilihat oleh pengguna
            )
            return

        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            # Jika bot sudah ada di voice channel, pindahkan bot ke channel pengguna
            await voice_client.move_to(channel)
            await interaction.response.send_message(f"Move to {channel.mention}!")
        else:
            # Jika bot belum ada di voice channel mana pun, koneksikan bot
            await channel.connect()
            await interaction.response.send_message(f"Connected to {channel.mention}!")

    @app_commands.command(name="play", description="Play music dari YouTube atau via pencarian")
    @app_commands.describe(query="Judul lagu atau URL yang ingin diputar")
    async def play(self, interaction: discord.Interaction, query: str):
        # 1. Defer response (WAJIB)
        # yt-dlp melakukan request jaringan yang butuh waktu lebih dari 3 detik.
        # Kita beri tahu Discord bahwa bot sedang memproses agar interaction tidak kadaluarsa/error.
        await interaction.response.defer()

        # 2. Sanitasi Input
        safe_query = self.sanitize_input(query)
        if not safe_query:
            await interaction.followup.send("Kueri pencarian tidak valid atau mengandung karakter terlarang.")
            return

        # 3. Pengecekan Voice Channel (seperti logika /join)
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("Kamu harus bergabung ke voice channel terlebih dahulu!")
            return

        channel = interaction.user.voice.channel
        global voice_client
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await channel.connect(self_deaf=True)
        elif voice_client.channel != channel:
            voice_client.stop()
            await voice_client.move_to(channel)

        # 4. Search menggunakan yt-dlp secara Asynchronous
        # Mengekstrak info jaringan tidak boleh memblokir event loop utama bot.
        # Oleh karena itu, kita masukkan fungsi yt_dlp ke dalam thread executor terpisah.
        loop = asyncio.get_event_loop()
        try:
            def extract_data():
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                    return ydl.extract_info(safe_query, download=False)

            data = await loop.run_in_executor(None, extract_data)
        except Exception as e:
            await interaction.followup.send(f"Terjadi kesalahan saat mencari lagu: `{str(e)}`")
            return

        # Jika hasilnya berupa list (hasil pencarian 'ytsearch'), ambil elemen pertama
        if 'entries' in data:
            data = data['entries'][0]

        audio_url = data['url']
        title = data['title']

        # 5. Lempar audio ke voice channel dengan FFmpeg
        if voice_client.is_playing():
            # Untuk skenario sederhana: Hentikan lagu yang sedang diputar.
            # (Jika ingin lebih kompleks, di sinilah kamu membuat logika antrean/queue array)
            voice_client.stop()

        try:
            # Gunakan FFmpegPCMAudio untuk melakukan konversi stream secara real-time
            audio_source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

            # Putar audio di voice channel
            voice_client.play(audio_source, after=lambda e: print(f'Player error: {e}') if e else None)

            # Kirim balasan sukses
            await interaction.followup.send(f"🎵 Sedang memutar: **{title}**")

        except Exception as e:
            await interaction.followup.send(f"Gagal memproses audio dengan FFmpeg: `{str(e)}`")

    @app_commands.command(name="pause", description="Pause music")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice_client.pause()
        await interaction.followup.send(f"Paused music!")

    @app_commands.command(name="resume", description="Resume music")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer()
        voice_client.resume()
        await interaction.followup.send(f"Resumed music!")

    @app_commands.command(name="stop", description="Stop music")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await voice_client.disconnect()
        await interaction.followup.send(f"Stopped music!")

async def setup(bot):
    await bot.add_cog(Music(bot))