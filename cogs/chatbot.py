from discord.ext import commands
from google.genai import types
from google import genai

class ChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_chat_id = bot.guild_chat_id
        self.client = genai.Client(api_key=bot.gemini_api_key)
        configuration = types.GenerateContentConfig(
            system_instruction=bot.gemini_global_instruction,)
        self.chat_session = self.client.chats.create(
            model="gemini-3.1-flash-lite",
            config=configuration,
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        for user in message.mentions:
            if user.id == self.bot.user.id and message.channel.id == self.guild_chat_id:
                chat_to_send = message.author.name + " : " + message.content
                response = self.chat_session.send_message(chat_to_send)
                await message.channel.send(response.text)

async def setup(bot):
    await bot.add_cog(ChatBot(bot))