import os
import google.generativeai as genai
from ai.base_client import BaseAIClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Safety設定 (元のgoogleAI.pyから)
SAFETY_CONFIG = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]


class GeminiClient(BaseAIClient):
    """Google Gemini API Client"""

    MODEL_NAME = "gemini-flash-latest"
    TEMPERATURE = 1.0
    MAX_OUTPUT_TOKENS = 200

    def __init__(self):
        super().__init__()
        api_key = os.getenv('GOOGLE_API_KEY')

        if not api_key:
            raise ValueError("GOOGLE_API_KEY が環境変数に設定されていません")

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(self.MODEL_NAME)
        self.generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=self.MAX_OUTPUT_TOKENS,
            temperature=self.TEMPERATURE
        )

        # 共通システムプロンプトで初期化
        initial_history = [
            {
                "role": "user",
                "parts": [{"text": self.SYSTEM_PROMPT}]
            },
            {
                "role": "model",
                "parts": [{"text": "承知しました。簡潔な回答を心がけ、表はアスキーアート形式で出力します。"}]
            }
        ]
        self.chat = self.model.start_chat(history=initial_history)

    def send_message(self, message: str) -> str:
        """Gemini APIにメッセージを送信して応答を取得"""
        try:
            response = self.chat.send_message(
                message,
                safety_settings=SAFETY_CONFIG,
                generation_config=self.generation_config
            )

            # 履歴が上限を超えたら削除
            self.prune_history()

            return self._make_answer(message, response.text)

        except Exception as e:
            logger.error(f"[GeminiClient] {type(e).__name__}: {str(e)}")
            raise

    def prune_history(self) -> None:
        """Gemini用の履歴削除 (システムプロンプト保持、最古のペアを削除)"""
        # システムプロンプト(最初の2メッセージ)を保持したまま削除
        if len(self.chat.history) > self.MAX_HISTORY_LENGTH + 2:
            # index 2以降から最古のuser-modelペアを削除
            if len(self.chat.history) >= 4:  # system(2) + user + model
                # index 2, 3を削除(システムプロンプトの次のペア)
                self.chat.history.pop(2)
                self.chat.history.pop(2)

                # 更新された履歴で新しいチャットを開始
                self.chat = self.model.start_chat(history=self.chat.history)
