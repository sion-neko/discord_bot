import os
from groq import Groq
from ai.base_client import BaseAIClient


class GroqClient(BaseAIClient):
    """Groq API Client (groq/compound-mini モデル使用)"""

    MODEL_NAME = "groq/compound-mini"
    TEMPERATURE = 1.0
    MAX_TOKENS = 1000

    def __init__(self):
        super().__init__()
        api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY が環境変数に設定されていません")

        # OpenAI SDKでGroq APIに接続
        self.client = Groq()

        self.chat_history = []  # フォーマット: [{"role": "user/assistant", "content": "..."}]

    def send_message(self, input_message: str) -> str | dict:
        """
        Groq Compound APIにメッセージを送信

        Returns:
            str: 通常の会話応答
            dict: Web検索結果 {"type": "search_result", "summary": "...", "search_results": [...], "query": "..."}
        """
        try:
            # ユーザーメッセージを履歴に追加
            user_msg = {"role": "user", "content": input_message}
            self.chat_history.append(user_msg)

            # Groq Compound APIを呼び出し
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=self.chat_history,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
                search_settings={
                    "country": "japan"
                }
            ).choices[0].message

            response_message = response.content

            # 通常の会話応答
            if response_message is None:
                print(f"[GroqClient] 警告: contentがNoneです。")
                response_message = "応答を生成できませんでした。"

            elif response.executed_tools:
                for result in response.executed_tools[0].search_results.results:
                    response_message += "\n" + result.url
            
        except Exception as e:
            print(f"[GroqClient] エラー: {type(e).__name__}: {str(e)}")
            raise  # 上位(AIManager)でフォールバック処理するため再raise

        assistant_msg = {"role": "assistant", "content": response_message}
        self.chat_history.append(assistant_msg)
        self.prune_history()

        return self._make_answer(input_message, response_message)

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
