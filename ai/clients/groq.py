import os
import json
from openai import OpenAI
from ai.base_client import BaseAIClient

# Web検索ツールの定義
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "最新の情報、ニュース、事実、データを検索します。ユーザーが最近の出来事や現在のデータ、具体的な事実情報を求めている場合に使用してください。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "検索クエリ(最適化された検索キーワード)"
                }
            },
            "required": ["query"]
        }
    }
}

class GroqClient(BaseAIClient):
    """Groq API Client (llama-3.3-70b-versatile モデル使用)"""

    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 1.0
    MAX_TOKENS = 1000

    def __init__(self):
        super().__init__()
        api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY が環境変数に設定されていません")

        # OpenAI SDKでGroq APIに接続
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.chat_history = []  # フォーマット: [{"role": "user/assistant", "content": "..."}]

    def send_message(self, message: str) -> str | dict:
        """
        Groq APIにメッセージを送信

        Returns:
            str: 通常の会話応答
            dict: Tool call要求 {"tool": "web_search", "query": "...", "tool_call_id": "..."}
        """
        try:
            # ユーザーメッセージを履歴に追加
            user_msg = {"role": "user", "content": message}
            self.chat_history.append(user_msg)

            # Groq APIを呼び出し (Function Calling有効)
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=self.chat_history,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                tools=[WEB_SEARCH_TOOL],  # ツールを追加
                tool_choice="auto"         # AIが自動判断
            )

            # Tool callがあるかチェック
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]

                if tool_call.function.name == "web_search":
                    args = json.loads(tool_call.function.arguments)

                    print(f"[GroqClient] Web検索要求: {args['query']}")

                    # Tool call情報を返す
                    return {
                        "tool": "web_search",
                        "query": args["query"],
                        "tool_call_id": tool_call.id,
                        "user_message": message  # 元のメッセージも保存
                    }

            # 通常の応答
            assistant_message = response.choices[0].message.content

            # アシスタント応答を履歴に追加
            assistant_msg = {"role": "assistant", "content": assistant_message}
            self.chat_history.append(assistant_msg)

            # 履歴が上限を超えたら削除
            self.prune_history()

            # Discord用にフォーマット
            return self._make_answer(message, assistant_message)

        except Exception as e:
            # リクエスト失敗時は追加したユーザーメッセージを削除
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history.pop()

            print(f"[GroqClient] エラー: {type(e).__name__}: {str(e)}")
            raise  # 上位(AIManager)でフォールバック処理するため再raise

    def prune_history(self) -> None:
        """Groq用の履歴削除 (最古のペアを削除)"""
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH:
            # 最古のuser-assistantペアを削除
            if len(self.chat_history) >= 2:
                self.chat_history.pop(0)  # 最古のユーザーメッセージ
                if self.chat_history:
                    self.chat_history.pop(0)  # 最古のアシスタントメッセージ
                print(f"[GroqClient] 会話履歴を削除しました")
            else:
                break
