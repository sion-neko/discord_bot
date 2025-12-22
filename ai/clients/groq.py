import os
from openai import OpenAI
from ai.base_client import BaseAIClient

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

    def send_message(self, message: str) -> str:
        """Groq APIにメッセージを送信して応答を取得"""
        try:
            # ユーザーメッセージを履歴に追加
            user_msg = {"role": "user", "content": message}
            self.chat_history.append(user_msg)

            # Groq APIを呼び出し
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=self.chat_history,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS
            )

            # 応答テキストを抽出
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
