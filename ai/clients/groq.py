import os
from openai import OpenAI
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
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.chat_history = []  # フォーマット: [{"role": "user/assistant", "content": "..."}]

    def send_message(self, message: str) -> str | dict:
        """
        Groq Compound APIにメッセージを送信

        Returns:
            str: 通常の会話応答
            dict: Web検索結果 {"type": "search_result", "summary": "...", "citations": [...], "query": "..."}
        """
        try:
            # ユーザーメッセージを履歴に追加
            user_msg = {"role": "user", "content": message}
            self.chat_history.append(user_msg)

            # Groq Compound APIを呼び出し
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=self.chat_history,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS
            )

            message_obj = response.choices[0].message
            content = message_obj.content

            # executed_toolsを取得
            executed_tools = getattr(message_obj, 'executed_tools', None)

            # Web検索が実行された場合
            if executed_tools and len(executed_tools) > 0:
                search_results = executed_tools[0].search_results
                citations = self._extract_citations(search_results)

                print(f"[GroqClient] Web search performed")

                assistant_msg = {"role": "assistant", "content": content or "検索結果を取得しました"}
                self.chat_history.append(assistant_msg)
                self.prune_history()

                return {
                    "type": "search_result",
                    "summary": content,
                    "citations": citations,
                    "query": message
                }

            # 通常の会話応答
            if content is None:
                print(f"[GroqClient] 警告: contentがNoneです。")
                content = "応答を生成できませんでした。"

            assistant_msg = {"role": "assistant", "content": content}
            self.chat_history.append(assistant_msg)
            self.prune_history()

            return self._make_answer(message, content)

        except Exception as e:
            # リクエスト失敗時は追加したユーザーメッセージを削除
            if self.chat_history and self.chat_history[-1]["role"] == "user":
                self.chat_history.pop()

            print(f"[GroqClient] エラー: {type(e).__name__}: {str(e)}")
            raise  # 上位(AIManager)でフォールバック処理するため再raise

    def _extract_citations(self, search_results) -> list[str]:
        """search_resultsからURLを抽出"""
        citations = []

        try:
            if isinstance(search_results, list):
                for result in search_results:
                    # 辞書の'url'キー
                    if isinstance(result, dict) and 'url' in result:
                        citations.append(result['url'])
                    # オブジェクトの.url属性
                    elif hasattr(result, 'url'):
                        citations.append(result.url)

            print(f"[GroqClient] Extracted {len(citations)} citations")

        except Exception as e:
            print(f"[GroqClient] Citation extraction error: {e}")

        return citations

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
