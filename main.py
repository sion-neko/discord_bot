import os
import sys
import random
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

import api
import googleAI
from keep_alive import keep_alive

# --- Constants ---
ERROR_CODE = -1
ERROR_EMBED_COLOR = 0xff0000
SMASH_BROS_CHARACTERS_FILE = "./data/smabra.txt"

# --- Environment Variables ---
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# --- Global Instances ---
api_client = api.API()
gemini_client = googleAI.Gemini()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents)

# --- Embeds ---
ERROR_EMBED = discord.Embed(
    title="Error!",
    color=ERROR_EMBED_COLOR,
    description="エラーが発生しました。管理者に連絡してください。\n"
)

# --- Bot Event Handlers ---
@bot.event
async def on_ready():
    """Called when the bot is ready and online."""
    for guild in bot.guilds:
        await bot.tree.sync(guild=discord.Object(id=guild.id))

    gemini_client.zunda_initialize()
    # await bot.tree.sync() # Syncing per guild is generally preferred
    print(f"Python version: {sys.version}")
    print(f"{bot.user}: Bot startup complete.")

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Handles errors that occur during command execution."""
    original_error = getattr(error, "original", error)
    error_msg = "".join(traceback.TracebackException.from_exception(original_error).format())
    print(f"An error occurred: {error_msg}")
    await ctx.send(embed=ERROR_EMBED)

# --- Bot Commands ---
@bot.tree.command(name="talk", description="ずんだもんとおしゃべり")
async def talk(interaction: discord.Interaction, message: str):
    """Allows users to talk with Zundamon via the Gemini AI."""
    await interaction.response.defer(thinking=True)
    response = gemini_client.char_talk(message)
    if response == ERROR_CODE:
        display_message = f"> {message}"
        await interaction.followup.send(display_message, embed=ERROR_EMBED)
    else:
        await interaction.followup.send(response)

@bot.tree.command(name="r", description="数字をランダム出力")
async def random_number(interaction: discord.Interaction, num: int):
    """Generates a random number up to the specified limit."""
    if num <= 0:
        await interaction.response.send_message("正の整数を入力してください。", ephemeral=True)
        return
    result = random.randint(1, num)
    await interaction.response.send_message(str(result))

@bot.tree.command(name="r_sma", description="ずんだもんがスマブラSPのキャラを選ぶよ")
async def random_smash_char(interaction: discord.Interaction):
    """Randomly selects a Super Smash Bros. character."""
    try:
        with open(SMASH_BROS_CHARACTERS_FILE, "r", encoding="utf-8") as f:
            all_chara = [line.strip() for line in f if line.strip()]
        if not all_chara:
            await interaction.response.send_message("キャラクターリストが空です。", embed=ERROR_EMBED)
            return

        # Ensure chara_no is within the valid range of indices
        chara_no = random.randint(0, len(all_chara) - 1)
        result = all_chara[chara_no]
        await interaction.response.send_message(result)
    except FileNotFoundError:
        await interaction.response.send_message(f"{SMASH_BROS_CHARACTERS_FILE} が見つかりません。", embed=ERROR_EMBED)
    except Exception as e:
        print(f"Error in r_sma: {e}")
        await interaction.response.send_message(embed=ERROR_EMBED)


@bot.tree.command(name="dog", description="わんちゃん")
async def dog_image(interaction: discord.Interaction):
    """Fetches and sends a random dog image."""
    image_url = api_client.dog()
    if image_url == "取得できなかった": # Check for the specific error message from api.py
        await interaction.response.send_message(image_url, embed=ERROR_EMBED)
    elif image_url:
        await interaction.response.send_message(image_url)
    else:
        await interaction.response.send_message("犬の画像を取得できませんでした。", embed=ERROR_EMBED)

# --- Main Execution ---
if __name__ == "__main__":
    keep_alive()  # Start the web server to keep the bot alive
    try:
        if BOT_TOKEN is None:
            print("Error: BOT_TOKEN environment variable not set.")
            sys.exit(1)
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid bot token. Please check your BOT_TOKEN environment variable.")
        # The os.system("kill") is problematic. It's better to let the script exit.
        # Consider more robust process management if needed.
    except Exception as e:
        print(f"An unexpected error occurred during bot execution: {e}")
        # os.system("kill") # Avoid generic kill commands