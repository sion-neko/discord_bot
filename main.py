import os
import discord
from discord.ext.commands import Bot
import api
import googleAI
import traceback
from dotenv import load_dotenv
import random
from keep_alive import keep_alive

load_dotenv() 
API = api.API()
gem = googleAI.Gemini()
bot = Bot(command_prefix='$', intents=discord.Intents.all())
ERROR = -1
ERROR_EMBED = discord.Embed(title="Error!",color=0xff0000, description="エラーが発生しました。管理者に連絡してください。\n")


@bot.event
async def on_ready():
    for server in bot.guilds:
        await bot.tree.sync(guild=discord.Object(id=server.id))

    gem.musuka_initialize()
    gem.gemini_initialize()
    await bot.tree.sync()
    print(f"{bot.user}:起動完了")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    print(error_msg)
    await ctx.send(embed=ERROR_EMBED)


@bot.tree.command(name="talk", description="AIと会話")
async def talk(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    response = gem.gemini_talk(message)
    if response == ERROR:
        message = "> " + message
        await interaction.followup.send(message, embed=ERROR_EMBED)
    else:
        await interaction.followup.send(response)


@bot.tree.command(name="musuka", description="ムスカ大佐とお話♡")
async def char_talk(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)
    response = gem.char_talk(message)
    if response == ERROR:
        message = "> " + message
        await interaction.followup.send(message, embed=ERROR_EMBED)
    else:
        await interaction.followup.send(response)

@bot.tree.command(name="r", description="ランダムな数字を出力します")
async def r(interaction: discord.Interaction, num: int):
    result = random.randint(1, int(num))
    await interaction.response.send_message(result)

@bot.tree.command(name="dog", description="わんちゃん")
async def dog(interaction):
    res= API.dog()
    await interaction.response.send_message(res)


# Web サーバの立ち上げ
keep_alive()
try:
  bot.run(os.getenv('BOT_TOKEN'))
except:
  os.system("kill")