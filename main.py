import os
import discord
from discord.ext.commands import Bot
import api
from ai import AIManager, AIError
import traceback
import random
from keep_alive import keep_alive
import sys
import logging
from utils.logger import setup_logger

# アプリケーションロガーのセットアップ
logger = setup_logger(__name__)

# discord.pyのログを有効化
discord_logger = setup_logger('discord')
discord_logger.setLevel(logging.INFO)

API = api.API()
ai_mgr = AIManager()
bot = Bot(command_prefix='$', intents=discord.Intents.all())
ERROR_EMBED = discord.Embed(title="Error!",color=0xff0000, description="エラーが発生しました。管理者に連絡してください。\n")
DM_REJECTED_MESSAGE = "このBotとの会話はサーバーでのみ使用できます。"


@bot.event
async def on_ready():
    for server in bot.guilds:
        await bot.tree.sync(guild=discord.Object(id=server.id))

    await bot.tree.sync()
    logger.info(f"python-version：{sys.version}")
    logger.info(f"{bot.user}:起動完了")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    logger.error(error_msg)
    await ctx.send(embed=ERROR_EMBED)


@bot.tree.command(name="talk", description="AIアシスタントとおしゃべり")
async def talk(interaction: discord.Interaction, message: str):
    # DMからのコマンドは拒否
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    message_quoted = "> " + message
    try:
        response = ai_mgr.send_message(message)
        # /talkコマンドでは引用を付ける
        final_response = f"{message_quoted}\n\n{response}"
        await interaction.followup.send(final_response)
    except AIError as e:
        logger.error(f"[/talk] Error: {e}")
        await interaction.followup.send(message_quoted, embed=ERROR_EMBED)

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return

    # Botへのメンションをチェック
    if bot.user in message.mentions:
        # メンション文字列を除去
        content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        # 空メッセージの場合は定型文を返す
        if not content:
            await message.channel.send("何かご用ですか？")
            return

        # DMからは拒否
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send(DM_REJECTED_MESSAGE)
            return

        # タイピングインジケータを表示しながらAI応答取得と送信
        async with message.channel.typing():
            try:
                response = ai_mgr.send_message(content)
                await message.channel.send(response)
            except AIError as e:
                logger.error(f"[mention] Error: {e}")
                message_quoted = "> " + content
                await message.channel.send(message_quoted, embed=ERROR_EMBED)

@bot.tree.command(name="search", description="Webを検索して要約")
async def search(interaction: discord.Interaction, query: str):
    """Perplexity APIで直接Web検索"""
    # DMからのコマンドは拒否
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

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
        result = ai_mgr.perplexity_client.search(query)

        # 応答本文を取得
        response_text = result["content"]

        # 参照URLがある場合は追加
        citations = result.get("citations", [])
        if citations:
            response_text += "\n\n**参照:**"
            max_links = 3  # 上位3件に制限
            for i, url in enumerate(citations[:max_links], start=1):
                response_text += f"\n{i}. <{url}>"

        await interaction.followup.send(response_text)

    except Exception as e:
        logger.error(f"[/search] Error: {e}")
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
    logger.error("BOT_TOKENが設定されていません。.envファイルを確認してください。")
    sys.exit(1)

try:
    bot.run(bot_token)
except discord.LoginFailure:
    logger.error("BOT_TOKENが無効です。正しいトークンを.envファイルに設定してください。")
    sys.exit(1)
except Exception as e:
    logger.error(f"予期しないエラーが発生しました: {e}")
    traceback.print_exc()
    sys.exit(1)