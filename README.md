# Discord AI Bot

xAI GrokとPerplexityを統合したDiscordボットです。サーバー内でAIとの対話やWeb検索が可能です。

## 機能

- **AIチャット**: メンションまたは `/talk` コマンドでAIアシスタントと会話
- **Web検索**: `/search` コマンドでPerplexity APIを使用したWeb検索と要約（オプション）
- **画像検索**: `/image` コマンドでDuckDuckGo画像検索
- **リマインダー**: `/remind` で指定日時にメッセージを送信。メッセージ入力欄で`@`メンションを選択すればその相手にも通知される。一覧はサーバー全体で共有され、誰でも確認・キャンセルできる
- **ランダムコマンド**: `/r` で数字のランダム生成、`/r_sma` でスマブラキャラクター選択
- **犬画像取得**: `/dog` でランダムな犬の画像を取得

## 必要な環境

- Python 3.12以上（またはDocker）
- Discord Bot Token
- xAI API Key
- Perplexity API Key（`/search` コマンドを使う場合）

## セットアップ

### 環境変数の設定

プロジェクトルートに `.env` ファイルを作成し、以下の環境変数を設定してください。

```env
BOT_TOKEN=your_discord_bot_token_here
XAI_API_KEY=your_xai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here  # オプション
```

#### 各APIキーの取得方法

- **Discord Bot Token**: [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成し、Botトークンを取得
- **xAI API Key**: [xAI Console](https://console.x.ai/) で取得
- **Perplexity API Key**: [Perplexity API](https://www.perplexity.ai/) で取得

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
| `/remind <time> <message>` | 指定日時にメッセージを送信するリマインダーを設定（コマンド実行チャンネルに送信、送信時に設定者名を自動付記） | `/remind 2026-07-15 09:00 会議の時間です @taro` |
| `/remind_list [mine]` | サーバー全体の設定中リマインダー一覧を表示（`mine:true`で自分の分だけに絞り込み） | `/remind_list` |
| `/remind_cancel <no>` | リマインダーをキャンセル（誰でも取消可能） | `/remind_cancel 3` |
| `/r <num>` | 1からnumまでのランダムな整数を生成 | `/r 100` |
| `/r_sma` | スマブラSPのキャラクターをランダムに選択 | `/r_sma` |
| `/dog` | ランダムな犬の画像を取得 | `/dog` |

`time`は以下の形式に対応しています（すべてJST基準）:
- `YYYY-MM-DD HH:MM`（例: `2026-07-15 09:00`）
- `MM-DD HH:MM`（今年として解釈、例: `07-15 09:00`）
- `HH:MM`（今日。すでに過ぎていれば翌日、例: `09:00`）

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
├── reminder/            # リマインダー機能
│   ├── store.py         # SQLiteによる永続化
│   └── parser.py        # 日時文字列のパース
├── data/                # SQLiteデータベース（Gitには含まれません）
└── utils/
    └── logger.py        # ロガー設定
```

## 注意事項

- このBotはサーバー（Guild）でのみ動作し、DMには対応していません
- 各APIには使用制限がある場合があります。詳細は各サービスのドキュメントを参照してください
