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


def create_search_embed(result: dict) -> discord.Embed:
    """
    Perplexity検索結果をDiscord Embedに変換

    Args:
        result: {
            "summary": "要約テキスト",
            "citations": ["url1", "url2", ...],
            "query": "検索クエリ"
        }
    """
    # 要約が長すぎる場合は切り詰め
    summary = result["summary"]
    if len(summary) > 2000:
        summary = summary[:1997] + "..."

    embed = discord.Embed(
        title="🔍 Web検索結果",
        description=summary,
        color=0x00a67e  # Perplexityカラー
    )

    # 検索クエリを追加
    embed.add_field(
        name="検索クエリ",
        value=f"`{result['query']}`",
        inline=False
    )

    # 参照元URLを追加
    if result.get("citations"):
        citations_list = result["citations"][:5]  # 最大5件
        if citations_list:
            citations_text = "\n".join([
                f"{i+1}. [{url}]({url})"
                for i, url in enumerate(citations_list)
            ])
            embed.add_field(
                name="📚 参照元",
                value=citations_text,
                inline=False
            )

    embed.set_footer(text="Powered by Perplexity Sonar API")

    return embed


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

    # 検索結果の場合
    if isinstance(response, dict):
        if response.get("type") == "search_result":
            # Embed形式で表示
            embed = create_search_embed(response)
            await interaction.followup.send(embed=embed)
            return

        elif response.get("type") == "error":
            # エラーEmbed
            error_embed = discord.Embed(
                title="検索エラー",
                description=response["message"],
                color=0xff0000
            )
            await interaction.followup.send(embed=error_embed)
            return

    # 通常の会話応答
    if response == ERROR or "エラーが発生しました" in response:
        message_quoted = "> " + message
        await interaction.followup.send(message_quoted, embed=ERROR_EMBED)
    else:
        await interaction.followup.send(response)

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