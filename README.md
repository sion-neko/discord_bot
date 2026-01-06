# Discord AI Bot

複数のAI APIと統合されたDiscordボットです。Gemini、Groq、Perplexityなどの最新AIサービスを利用して、サーバー内でAIとの対話やWeb検索が可能です。

## 機能

- **AIチャット**: メンションまたは `/talk` コマンドでAIアシスタントと会話
- **Web検索**: `/search` コマンドでPerplexity APIを使用したWeb検索と要約
- **ランダムコマンド**: `/r` で数字のランダム生成、`/r_sma` でスマブラキャラクター選択
- **犬画像取得**: `/dog` でランダムな犬の画像を取得

## 必要な環境

- Python 3.12以上
- Discord Bot Token
- 各種APIキー（Gemini、Groq、Perplexity）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <このリポジトリのURL>
cd 8_discord_bot
```

### 2. 仮想環境の作成とアクティベート

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定してください。

```env
BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

#### 各APIキーの取得方法

- **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成し、Botトークンを取得
- **Gemini API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey) で取得
- **Groq API Key**: [Groq Console](https://console.groq.com/) で取得
- **Perplexity API Key**: [Perplexity API](https://www.perplexity.ai/) で取得

### 5. Botの起動

```bash
python main.py
```

## 使用方法

### コマンド一覧

| コマンド | 説明 | 使用例 |
|---------|------|--------|
| `/talk <message>` | AIアシスタントと会話 | `/talk こんにちは` |
| `/search <query>` | Webを検索して要約 | `/search Python 最新情報` |
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
8_discord_bot/
├── main.py              # メインのBotロジック
├── api.py               # 外部API（犬画像など）のラッパー
├── keep_alive.py        # Flaskサーバー（ヘルスチェック用）
├── requirements.txt     # Python依存関係
├── .env                 # 環境変数（Gitには含まれません）
├── .gitignore          # Git除外設定
├── ai/                  # AI関連モジュール
│   ├── __init__.py      # AIモジュールのエクスポート
│   ├── manager.py       # AIクライアントの管理
│   ├── base_client.py   # AIクライアントの基底クラス
│   ├── exceptions.py    # カスタム例外
│   └── clients/         # 各AIサービスのクライアント実装
│       ├── __init__.py
│       ├── gemini.py    # Google Gemini API
│       ├── groq.py      # Groq API（Function Calling対応）
│       └── perplexity.py # Perplexity API
└── data/
    └── smabra.txt       # スマブラキャラクターリスト
```

## 注意事項

- このBotはサーバー（Guild）でのみ動作し、DMには対応していません
- 各APIには使用制限がある場合があります。詳細は各サービスのドキュメントを参照してください
