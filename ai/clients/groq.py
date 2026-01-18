import os
import time
from groq import Groq
from ai.base_client import BaseAIClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


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
        self.last_message_time: float | None = None

    def send_message(self, input_message: str) -> str | dict:
        """
        Groq Compound APIにメッセージを送信

        Returns:
            str: 通常の会話応答
            dict: Web検索結果 {"type": "search_result", "summary": "...", "search_results": [...], "query": "..."}
        """
        # ユーザーメッセージを履歴に追加
        user_msg = {"role": "user", "content": input_message}
        self.chat_history.append(user_msg)
        self.last_message_time = time.time()

        # 24時間以上経過していたら履歴を全削除
        if self.last_message_time:
            elapsed = time.time() - self.last_message_time
            if elapsed > 24 * 60 * 60:
                self.chat_history = [self.chat_history[0]]  # systemのみ保持
                logger.info("[GroqClient] 24時間経過のため履歴をクリア")
                return

        try:
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

            # 成功時: 履歴に追加して返す
            assistant_msg = {"role": "assistant", "content": response_message}
            self.chat_history.append(assistant_msg)
            self.prune_history()
            return self._make_answer(input_message, response_message)

        except Exception as e:
            if self._is_413_error(e) and self._reduce_history():
                logger.warning("[GroqClient] 413エラー検出、履歴を削減してリトライ")
                return self.send_message(input_message)

            # 413以外のエラー、または履歴削減不可
            logger.error(f"[GroqClient] {type(e).__name__}: {str(e)}")
            # 失敗したユーザーメッセージを履歴から削除
            if self.chat_history and self.chat_history[-1].get("role") == "user":
                self.chat_history.pop()
            raise

    def prune_history(self) -> None:
        """Groq用の履歴削除 (システムメッセージを保持)"""
        # システムメッセージ(index 0)を保持したまま削除
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH + 1:
            # system + user + assistant の最低3件必要
            if len(self.chat_history) >= 3:
                self.chat_history.pop(1)  # index 1 (最古のユーザーメッセージ)
                if len(self.chat_history) > 2:
                    self.chat_history.pop(1)  # 最古のアシスタントメッセージ
            else:
                break

    def _is_413_error(self, e: Exception) -> bool:
        """413エラー（Payload Too Large）かどうか判定"""
        error_str = str(e)
        error_type = type(e).__name__
        return ("413" in error_str) or ("PayloadTooLarge" in error_type) or ("RequestEntityTooLarge" in error_type)

    def _reduce_history(self) -> bool:
        """
        履歴を半分に減らす（systemメッセージは保持）

        Returns:
            bool: 削減できた場合True、これ以上削減できない場合False
        """
        # system + 最新のuser の最低2件は必要
        if len(self.chat_history) <= 2:
            return False
        # 保持する件数 = system(1) + 残りの半分
        keep_count = max(2, (len(self.chat_history) - 1) // 2 + 1)
        self.chat_history = [self.chat_history[0]] + self.chat_history[-keep_count + 1:]
        logger.info(f"[GroqClient] 履歴を{keep_count}件に削減")
        return True
