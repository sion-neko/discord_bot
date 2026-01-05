import os
import discord
from discord.ext.commands import Bot
import api
from ai import AIManager
import traceback
import random
from keep_alive import keep_alive
import sys

API = api.API()
ai_mgr = AIManager()
bot = Bot(command_prefix='$', intents=discord.Intents.all())
ERROR = -1
ERROR_EMBED = discord.Embed(title="Error!",color=0xff0000, description="エラーが発生しました。管理者に連絡してください。\n")


@bot.event
async def on_ready():
    for server in bot.guilds:
        await bot.tree.sync(guild=discord.Object(id=server.id))

    await bot.tree.sync()
    print("python-version："+sys.version)
    print(f"{bot.user}:起動完了")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    print(error_msg)
    await ctx.send(embed=ERROR_EMBED)


@bot.tree.command(name="talk", description="AIアシスタントとおしゃべり")
async def talk(interaction: discord.Interaction, message: str):
    await interaction.response.defer(thinking=True)

    response = ai_mgr.send_message(message)

    if response == ERROR or "エラーが発生しました" in response:
        message_quoted = "> " + message
        await interaction.followup.send(message_quoted, embed=ERROR_EMBED)
    else:
        await interaction.followup.send(response)

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # Botへのメンションをチェック
    if bot.user in message.mentions:
        content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        # 引数が空の場合は定型文を返す
        if not content:
            await message.channel.send("何かご用ですか？")
            return

        # タイピングインジケータを表示
        async with message.channel.typing():
            response = ai_mgr.send_message(content)

            if response == ERROR or "エラーが発生しました" in response:
                message_quoted = "> " + content
                await message.channel.send(message_quoted, embed=ERROR_EMBED)
            else:
                await message.channel.send(response)

@bot.tree.command(name="search", description="Webを検索して要約")
async def search(interaction: discord.Interaction, query: str):
    """Perplexity APIで直接Web検索"""
    await interaction.response.defer(thinking=True)

    # Perplexityが利用可能かチェック
    if not ai_mgr.perplexity_client:
        error_embed = discord.Embed(
            title="検索エラー",
            description="Web検索機能が利用できません。",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)
        return

    try:
        # Perplexityで直接検索
        print(f"[/search] Perplexity検索実行: {query}")
        result = ai_mgr.perplexity_client.search(query)

        # 検索結果をEmbedで表示
        await interaction.followup.send(result["content"])

    except Exception as e:
        print(f"[/search] 検索失敗: {e}")
        error_embed = discord.Embed(
            title="検索エラー",
            description=f"検索中にエラーが発生しました: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(name="r", description="数字をランダム出力")
async def r(interaction: discord.Interaction, num: int):
    result = random.randint(1, int(num))
    await interaction.response.send_message(result)

@bot.tree.command(name="r_sma", description="ずんだもんがスマブラSPのキャラを選ぶよ")
async def r_suma(interaction):
    with open("./data/smabra.txt") as f:
            all_chara = f.readlines()
    chara_no = random.randint(1, len(all_chara))

    result = all_chara[chara_no]

    await interaction.response.send_message(result)

@bot.tree.command(name="dog", description="わんちゃん")
async def dog(interaction):
    res= API.dog()
    await interaction.response.send_message(res)


# Web サーバの立ち上げ
keep_alive()

# BOT_TOKENの確認
bot_token = os.getenv('BOT_TOKEN')
if not bot_token:
    print("ERROR: BOT_TOKENが設定されていません。.envファイルを確認してください。")
    sys.exit(1)

try:
    bot.run(bot_token)
except discord.LoginFailure:
    print("ERROR: BOT_TOKENが無効です。正しいトークンを.envファイルに設定してください。")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: 予期しないエラーが発生しました: {e}")
    traceback.print_exc()
    sys.exit(1)