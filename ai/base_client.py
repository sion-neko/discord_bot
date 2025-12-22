from abc import ABC, abstractmethod
from typing import List, Dict


class BaseAIClient(ABC):
    """AI Clientの抽象基底クラス (Groq, Gemini, etc.)"""

    MAX_HISTORY_LENGTH = 20  # クラス定数: 会話履歴の最大長

    def __init__(self):
        self.chat_history: List[Dict] = []

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

    def get_history_length(self) -> int:
        """現在の会話履歴の長さを返す"""
        return len(self.chat_history)

    def _make_answer(self, user_msg: str, response: str) -> str:
        """Discord用に応答をフォーマット (ユーザーメッセージを引用)"""
        return f"> {user_msg}\n\n{response}"

    def prune_history(self) -> None:
        """履歴が上限を超えたら最古のメッセージを削除"""
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH:
            # 最古のペア(user + assistant)を削除
            if len(self.chat_history) >= 2:
                self.chat_history.pop(0)
                self.chat_history.pop(0)
                print(f"[{self.__class__.__name__}] 会話履歴を削除しました")
            else:
                break
