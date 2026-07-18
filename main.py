import os
import discord
from discord import app_commands
from discord.ext.commands import Bot
from discord.ext import tasks
import api
from ai import AIManager, AIError
from reminder import JST, ReminderStore, ReminderTimeError, parse_datetime
import traceback
import random
from datetime import datetime, timezone
from ddgs import DDGS

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
reminder_store = ReminderStore()
bot = Bot(command_prefix='$', intents=discord.Intents.all())
ERROR_EMBED = discord.Embed(
    title="Error!", color=0xff0000, description="エラーが発生しました。管理者に連絡してください。\n")
DM_REJECTED_MESSAGE = "このBotとの会話はサーバーでのみ使用できます。"
SUMABRA_CHARA = ["マリオ", "マルス", "ピクミン&オリマー", "クラウド", "ドンキーコング", "ルキナ", "ルカリオ", "カムイ", "リンク", "こどもリンク", "ロボット", "ベヨネッタ", "サムス", "ガノンドロフ", "トゥーンリンク", "インクリング", "ダークサムス", "ミュウツー", "ウルフ", "リドリー", "ヨッシー", "ロイ", "むらびと", "シモン", "カービィ", "クロム", "ロックマン", "リヒター", "フォックス", "Mr.ゲーム&ウォッチ", "Wii Fit トレーナー", "キングクルール", "ピカチュウ", "メタナイト", "ロゼッタ&チコ", "しずえ", "ルイージ", "ピット", "リトル・マック", "ガオガエン", "ネス", "ブラックピット", "ゲッコウガ",
                 "パックンフラワー", "キャプテン・ファルコン", "ゼロスーツサムス", "格闘Mii", "ジョーカー", "プリン", "ワリオ", "剣術Mii", "勇者", "ピーチ", "スネーク", "射撃Mii", "バンジョー&カズーイ", "デイジー", "アイク", "パルテナ", "テリー", "クッパ", "ゼニガメ", "パックマン", "ベレト／ベレス", "アイスクライマー", "フシギソウ", "ルフレ", "ミェンミェン", "シーク", "リザードン", "シュルク", "スティーブ／アレックス", "ゼルダ", "ディディーコング", "クッパ Jr.", "セフィロス", "ドクターマリオ", "リュカ", "ダックハント", "ホムラ", "ピチュー", "ソニック", "リュウ", "ヒカリ", "ファルコ", "デデデ", "ケン", "カズヤ", "ソラ"]


@bot.event
async def on_ready():
    for server in bot.guilds:
        await bot.tree.sync(guild=discord.Object(id=server.id))

    await bot.tree.sync()

    await reminder_store.init()
    if not check_reminders.is_running():
        check_reminders.start()

    logger.info(f"python-version：{sys.version}")
    logger.info(f"{bot.user}:起動完了")


@tasks.loop(seconds=30)
async def check_reminders():
    try:
        due = await reminder_store.get_due(datetime.now(timezone.utc))
    except Exception as e:
        logger.error(f"[reminder] 取得エラー: {e}")
        return

    for reminder in due:
        await reminder_store.delete(reminder.id)
        channel = bot.get_channel(reminder.channel_id)
        if channel is None:
            logger.warning(
                f"[reminder] channel not found id={reminder.id} channel_id={reminder.channel_id}")
            continue
        creator = _display_name(channel.guild, reminder.user_id) if channel.guild else str(reminder.user_id)
        content = f"{reminder.message}\n\n-# ⏰ リマインダー • {creator}が設定"
        try:
            await channel.send(content)
        except discord.HTTPException as e:
            logger.error(f"[reminder] 送信エラー id={reminder.id}: {e}")


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(
        traceback.TracebackException.from_exception(orig_error).format())
    logger.error(error_msg)
    await ctx.send(embed=ERROR_EMBED)


@bot.tree.command(name="talk", description="AIアシスタントとおしゃべり")
async def talk(interaction: discord.Interaction, message: str, image: discord.Attachment = None):
    logger.info(
        f"[/talk] user={interaction.user} guild={interaction.guild} message={message[:50]}")
    await interaction.response.defer(thinking=True)
    # DMからのコマンドは拒否
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.followup.send(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    image_url = image.url if image else None
    message_quoted = "> " + message
    try:
        response = ai_mgr.send_message(message, image_url=image_url)
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
        content = message.content.replace(
            f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        # 空メッセージの場合は定型文を返す
        if not content:
            await message.channel.send("何かご用ですか？")
            return

        # DMからは拒否
        if isinstance(message.channel, discord.DMChannel):
            await message.channel.send(DM_REJECTED_MESSAGE)
            return

        # タイピングインジケータを表示しながらAI応答取得と送信
        logger.info(
            f"[mention] user={message.author} guild={message.guild} message={content[:50]}")
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
    logger.info(
        f"[/search] user={interaction.user} guild={interaction.guild} query={query[:50]}")
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

    query_quoted = f"> {query}"

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

        # 検索クエリの引用を追加
        final_response = f"{query_quoted}\n\n{response_text}"
        await interaction.followup.send(final_response)

    except Exception as e:
        logger.error(f"[/search] Error: {e}")
        error_embed = discord.Embed(
            title="検索エラー",
            description=f"検索中にエラーが発生しました: {str(e)}",
            color=0xff0000
        )
        await interaction.followup.send(query_quoted, embed=error_embed)


@bot.tree.command(name="image", description="画像を検索")
async def image(interaction: discord.Interaction, query: str):
    logger.info(
        f"[/image] user={interaction.user} guild={interaction.guild} query={query[:50]}")
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))

        if not results:
            await interaction.followup.send(f"> {query}\n\n画像が見つかりませんでした。")
            return

        img = results[0]
        embed = discord.Embed(title=img.get("title", query), color=0x5865F2)
        embed.set_image(url=img["image"])
        embed.set_footer(text=f"検索: {query} | 出典: {img.get('source', '')}")
        await interaction.followup.send(f"> {query}", embed=embed)

    except Exception as e:
        logger.error(f"[/image] Error: {e}")
        await interaction.followup.send(
            f"> {query}",
            embed=discord.Embed(title="検索エラー", description=str(e), color=0xff0000)
        )


@bot.tree.command(name="r", description="数字をランダム出力")
async def r(interaction: discord.Interaction, num: int):
    logger.info(f"[/r] user={interaction.user} num={num}")
    result = random.randint(1, int(num))
    await interaction.response.send_message(result)


@bot.tree.command(name="r_sma", description="スマブラSPのキャラクターをランダム選択")
async def r_suma(interaction):
    logger.info(f"[/r_sma] user={interaction.user}")
    chara_no = random.randint(0, len(SUMABRA_CHARA)-1)
    chara = SUMABRA_CHARA[chara_no]
    await interaction.response.send_message(chara)


def _display_name(guild: discord.Guild, user_id: int) -> str:
    member = guild.get_member(user_id)
    return member.display_name if member else f"<@{user_id}>"


@bot.tree.command(name="remind", description="指定した日時にメッセージを送信するリマインダーを設定")
@app_commands.describe(message="改行したい場合は \\n（または ¥n）と入力してください")
async def remind(interaction: discord.Interaction, time: str, message: str):
    logger.info(
        f"[/remind] user={interaction.user} guild={interaction.guild} time={time} message={message[:50]}")
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    try:
        remind_at = parse_datetime(time)
    except ReminderTimeError as e:
        await interaction.response.send_message(str(e), ephemeral=True)
        return

    # 日本語キーボードでは \ キーが円記号(¥, U+00A5)として入力される環境があるため両対応
    message = message.replace("\\n", "\n").replace("¥n", "\n")
    reminder_id = await reminder_store.add(
        guild_id=interaction.guild.id,
        channel_id=interaction.channel.id,
        user_id=interaction.user.id,
        message=message,
        remind_at=remind_at,
    )

    # サーバー全体の並び順に基づく表示用番号を算出（/remind_list, /remind_cancelと共通の番号体系）
    reminders = await reminder_store.list_by_guild(interaction.guild.id)
    display_no = next((i for i, r in enumerate(reminders, start=1)
                       if r.id == reminder_id), len(reminders))

    remind_at_jst = remind_at.astimezone(JST)
    embed = discord.Embed(title="リマインダーを設定しました", color=0x57F287)
    embed.set_author(name=f"No. {display_no}")
    embed.add_field(name="日時", value=remind_at_jst.strftime('%Y-%m-%d %H:%M'), inline=False)
    embed.add_field(name="内容", value=message, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="remind_list", description="設定中のリマインダー一覧を表示（サーバー全体）")
@app_commands.describe(mine="自分が設定したものだけに絞り込むか")
async def remind_list(interaction: discord.Interaction, mine: bool = False):
    logger.info(f"[/remind_list] user={interaction.user} guild={interaction.guild} mine={mine}")
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    reminders = await reminder_store.list_by_guild(interaction.guild.id)
    numbered = list(enumerate(reminders, start=1))
    if mine:
        numbered = [(no, r) for no, r in numbered if r.user_id == interaction.user.id]

    title = "リマインダー一覧（自分の分）" if mine else "リマインダー一覧（サーバー全体）"
    embed = discord.Embed(title=title, color=0x5865F2)

    if not numbered:
        embed.description = "設定中のリマインダーはありません。"
        await interaction.response.send_message(embed=embed)
        return

    for no, r in numbered:
        remind_at_jst = r.remind_at.astimezone(JST)
        oneline_message = r.message.replace("\n", " / ")
        preview = oneline_message if len(oneline_message) <= 50 else oneline_message[:50] + "…"
        creator = _display_name(interaction.guild, r.user_id)
        embed.add_field(
            name=f"No. {no}",
            value=f"{remind_at_jst.strftime('%Y-%m-%d %H:%M')} ・ 設定: {creator}\n{preview}",
            inline=False,
        )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="remind_cancel", description="リマインダーをキャンセル")
@app_commands.describe(no="/remind_list で確認できる番号")
async def remind_cancel(interaction: discord.Interaction, no: int):
    logger.info(f"[/remind_cancel] user={interaction.user} no={no}")
    if isinstance(interaction.channel, discord.DMChannel):
        await interaction.response.send_message(DM_REJECTED_MESSAGE, ephemeral=True)
        return

    reminders = await reminder_store.list_by_guild(interaction.guild.id)
    if no < 1 or no > len(reminders):
        await interaction.response.send_message("指定された番号のリマインダーが見つかりません。", ephemeral=True)
        return

    target = reminders[no - 1]
    await reminder_store.delete(target.id)
    oneline_message = target.message.replace("\n", " / ")
    preview = oneline_message if len(oneline_message) <= 50 else oneline_message[:50] + "…"

    embed = discord.Embed(title="リマインダーをキャンセルしました", color=0xE67E22)
    embed.set_author(name=f"No. {no}")
    embed.add_field(name="内容", value=preview, inline=False)
    embed.add_field(name="キャンセル者", value=interaction.user.display_name, inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="dog", description="わんちゃん")
async def dog(interaction):
    await interaction.response.defer()
    logger.info(f"[/dog] user={interaction.user}")
    res = API.dog()
    await interaction.followup.send(res)

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
