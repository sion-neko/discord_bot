from abc import ABC, abstractmethod
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAIClient(ABC):
    """AI Clientの抽象基底クラス (Groq, Gemini, etc.)"""

    MAX_HISTORY_LENGTH = 20  # クラス定数: 会話履歴の最大長

    # 共通システムプロンプト
    SYSTEM_PROMPT = (
        "あなたは簡潔な回答を提供するアシスタントです。ユーザーからのメッセージを理解し、簡潔に回答してください。"
        "特に、Web検索を実行した場合は、検索結果を1-2文で要約し、要点のみを述べてください。\n\n"
        "重要: 表を出力する場合、Markdown形式(|で区切る形式)ではなく、"
        "見やすいアスキーアート的な形式で出力してください。例:\n"
        "良い例:\n"
        "┌────────┬────────┐\n"
        "│ 項目   │ 値     │\n"
        "├────────┼────────┤\n"
        "│ 名前   │ 太郎   │\n"
        "└────────┴────────┘\n\n"
        "悪い例:\n"
        "| 項目 | 値 |\n"
        "|------|----|\n"
        "| 名前 | 太郎 |"
    )

    @abstractmethod
    def send_message(self, message: str) -> str:
        """
        AIにメッセージを送信して応答を取得

        Args:
            message: ユーザーのメッセージ

        Returns:
            AIの応答テキスト

        Raises:
            Exception: API呼び出しエラー時
        """
        pass

    def _make_answer(self, user_msg: str, response: str) -> str:
        """Discord用に応答をフォーマット"""
        # モデル名を斜体で追加 (Discordマークダウン: *text*)
        model_signature = f"\n\n\-  *{self.MODEL_NAME}*"
        formatted = f"{response}{model_signature}"

        # Discordの2000文字制限に対応
        if len(formatted) > 2000:
            max_response_len = 2000 - len(model_signature) - 3
            truncated_response = response[:max_response_len] + "..."
            formatted = f"{truncated_response}{model_signature}"

        return formatted

    def prune_history(self) -> None:
        """履歴が上限を超えたら最古のメッセージを削除"""
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH:
            # 最古のペア(user + assistant)を削除
            if len(self.chat_history) >= 2:
                self.chat_history.pop(0)
                self.chat_history.pop(0)
                logger.debug(f"[{self.__class__.__name__}] 会話履歴を削除しました")
            else:
                break
