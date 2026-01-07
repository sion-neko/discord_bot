import os
from groq import Groq
from ai.base_client import BaseAIClient
from utils.logger import get_logger

logger = get_logger(__name__)


class GroqClient(BaseAIClient):
    """Groq API Client (groq/compound-mini モデル使用)"""

    MODEL_NAME = "groq/compound-mini"
    TEMPERATURE = 1.0
    MAX_TOKENS = 200

    def __init__(self):
        super().__init__()
        api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY が環境変数に設定されていません")

        # OpenAI SDKでGroq APIに接続
        self.client = Groq()

        # 共通システムプロンプトを使用
        self.chat_history = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT
            }
        ]

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
                logger.warning(f"[GroqClient] 警告: contentがNoneです。")
                response_message = "応答を生成できませんでした。"

            elif response.executed_tools:
                # Discordマークダウン形式でURLを表示
                response_message += "\n\n**参照:**"

                results = response.executed_tools[0].search_results.results
                max_links = 3  # 上位3件に制限

                for i, result in enumerate(results[:max_links], start=1):
                    # タイトルを取得、なければフォールバック
                    title = result.title if hasattr(result, 'title') and result.title else f"参考{i}"

                    # 長いタイトルは切り詰め
                    if len(title) > 80:
                        title = title[:77] + "..."

                    # Discordマークダウン形式
                    response_message += f"\n{i}. [{title}]({result.url})"
            
        except Exception as e:
            logger.error(f"[GroqClient] エラー: {type(e).__name__}: {str(e)}")
            raise  # 上位(AIManager)でフォールバック処理するため再raise

        assistant_msg = {"role": "assistant", "content": response_message}
        self.chat_history.append(assistant_msg)
        self.prune_history()

        return self._make_answer(input_message, response_message)

    def prune_history(self) -> None:
        """Groq用の履歴削除 (システムメッセージを保持)"""
        # システムメッセージ(index 0)を保持したまま削除
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH + 1:
            # system + user + assistant の最低3件必要
            if len(self.chat_history) >= 3:
                self.chat_history.pop(1)  # index 1 (最古のユーザーメッセージ)
                if len(self.chat_history) > 2:
                    self.chat_history.pop(1)  # 最古のアシスタントメッセージ
                logger.debug(f"[GroqClient] 会話履歴を削除しました")
            else:
                break
