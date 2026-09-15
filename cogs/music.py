import discord
import nacl
import davey
import yt_dlp
import asyncio
import re
from discord.ext import commands
from discord import app_commands, voice_client

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
        self.voice_client = None

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

    async def _internal_join(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel
        self.voice_client = interaction.guild.voice_client
        if self.voice_client:
            self.voice_client = await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

    @app_commands.command(name="join", description="Join to voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("Kamu harus di VC dulu!")
            return

        await interaction.response.defer()
        await self._internal_join(interaction)  # Memanggil logika internal
        await interaction.followup.send(f"Berhasil masuk ke {interaction.user.voice.channel.name}")

    async def play_music(self, interaction):
        data = await music_queue.get()
        audio_url = data['url']
        title = data['title']
        try:
            # Gunakan FFmpegPCMAudio untuk melakukan konversi stream secara real-time
            audio_source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)

            # Putar audio di voice channel
            self.voice_client.play(
                audio_source,
                after=lambda error: self.start_music(interaction, error)
            )

            # Kirim balasan sukses
            await interaction.followup.send(f"🎵 Sedang memutar: **{title}**")

        except Exception as e:
            await interaction.followup.send(f"Gagal memproses audio dengan FFmpeg: `{str(e)}`")

    def start_music(self, interaction, error=None):
        if error:
            print(f"Error saat memutar lagu: {error}")

        # Solusi utama: Masukkan fungsi async ke dalam loop discord yang sedang berjalan
        # Asumsi: Anda menyimpan instance bot di `self.bot` (misal saat __init__)
        self.bot.loop.create_task(self.play_music(interaction))

    @app_commands.command(name="play", description="Play music dari YouTube atau via pencarian")
    @app_commands.describe(query="Judul lagu atau URL yang ingin diputar")
    async def play(self, interaction: discord.Interaction, query: str):
        # 1. Defer response (WAJIB)
        # yt-dlp melakukan request jaringan yang butuh waktu lebih dari 3 detik.
        # Kita beri tahu Discord bahwa bot sedang memproses agar interaction tidak kadaluarsa/error.
        await interaction.response.defer()

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("Anda harus masuk ke voice channel terlebih dahulu!")
            return

        channel = interaction.user.voice.channel
        if not self.voice_client or not self.voice_client.is_connected() or self.voice_client.channel != channel:
            # PANGGIL fungsi join di sini menggunakan await
            await self._internal_join(interaction)

        # 2. Sanitasi Input
        safe_query = self.sanitize_input(query)
        if not safe_query:
            await interaction.followup.send("Kueri pencarian tidak valid atau mengandung karakter terlarang.")
            return

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

        if not data:
            await interaction.followup.send(f"Lagu atau Url tidak ditemukan!")
            return

        global music_queue
        music_queue = asyncio.Queue()
        music_queue.put_nowait(data)

        # 5. Lempar audio ke voice channel dengan FFmpeg
        if self.voice_client.is_playing():
            # Untuk skenario sederhana: Hentikan lagu yang sedang diputar.
            # (Jika ingin lebih kompleks, di sinilah kamu membuat logiktitle = data['title']a antrean/queue array)
            return

        self.start_music(interaction)



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