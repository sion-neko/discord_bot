# Discord AI Bot

xAI GrokとPerplexityを統合したDiscordボットです。サーバー内でAIとの対話やWeb検索が可能です。

## 機能

- **AIチャット**: メンションまたは `/talk` コマンドでAIアシスタントと会話
- **Web検索**: `/search` コマンドでPerplexity APIを使用したWeb検索と要約（オプション）
- **画像検索**: `/image` コマンドでBing Image Search APIを使用した画像検索（オプション）
- **ランダムコマンド**: `/r` で数字のランダム生成、`/r_sma` でスマブラキャラクター選択
- **犬画像取得**: `/dog` でランダムな犬の画像を取得

## 必要な環境

- Python 3.12以上（またはDocker）
- Discord Bot Token
- xAI API Key
- Perplexity API Key（`/search` コマンドを使う場合）
- Bing Image Search API Key（`/image` コマンドを使う場合）

## セットアップ

### 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定してください。

```env
BOT_TOKEN=your_discord_bot_token_here
XAI_API_KEY=your_xai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here  # オプション
BING_IMAGE_SEARCH_API_KEY=your_bing_image_search_api_key_here  # オプション
```

#### 各APIキーの取得方法

- **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成し、Botトークンを取得
- **xAI API Key**: [xAI Console](https://console.x.ai/) で取得
- **Perplexity API Key**: [Perplexity API](https://www.perplexity.ai/) で取得
- **Bing Image Search API Key**: [Azure Portal](https://portal.azure.com/) でBing Search v7リソースを作成して取得（月1,000リクエストまで無料）

### Docker で起動（推奨）

```bash
docker compose up -d
```

### ローカルで起動

```bash
python3 -m venv venv
source venv/bin/activate  # Windowsは venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 使用方法

### コマンド一覧

| コマンド | 説明 | 使用例 |
|---------|------|--------|
| `/talk <message>` | AIアシスタントと会話 | `/talk こんにちは` |
| `/search <query>` | Webを検索して要約 | `/search Python 最新情報` |
| `/image <query>` | 画像を検索 | `/image 猫` |
| `/r <num>` | 1からnumまでのランダムな整数を生成 | `/r 100` |
| `/r_sma` | スマブラSPのキャラクターをランダムに選択 | `/r_sma` |
| `/dog` | ランダムな犬の画像を取得 | `/dog` |

### メンション

Botにメンション（`@Bot名`）することで、AIアシスタントと会話できます。

```
@YourBot こんにちは！
```

## プロジェクト構造

```
discord_bot/
├── main.py              # メインのBotロジック
├── api.py               # 外部API（犬画像など）のラッパー
├── requirements.txt     # Python依存関係
├── Dockerfile
├── docker-compose.yml
├── .env                 # 環境変数（Gitには含まれません）
├── ai/                  # AI関連モジュール
│   ├── manager.py       # AIクライアントの管理
│   ├── base_client.py   # AIクライアントの基底クラス
│   ├── exceptions.py    # カスタム例外
│   └── clients/
│       ├── grok.py      # xAI Grok API
│       └── perplexity.py # Perplexity API
└── utils/
    └── logger.py        # ロガー設定
```

## 注意事項

- このBotはサーバー（Guild）でのみ動作し、DMには対応していません
- 各APIには使用制限がある場合があります。詳細は各サービスのドキュメントを参照してください
