import os
from openai import OpenAI
from ai.base_client import BaseAIClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GrokClient(BaseAIClient):
    """xAI Grok API Client"""

    MODEL_NAME = "grok-3-mini"
    TEMPERATURE = 1.0
    MAX_TOKENS = 200

    def __init__(self):
        super().__init__()
        api_key = os.getenv('XAI_API_KEY')

        if not api_key:
            raise ValueError("XAI_API_KEY が環境変数に設定されていません")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )

        self.chat_history = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT
            }
        ]

    def send_message(self, input_message: str) -> str:
        user_msg = {"role": "user", "content": input_message}
        self.chat_history.append(user_msg)

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=self.chat_history,
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )

            response_message = response.choices[0].message.content or "応答を生成できませんでした。"

            assistant_msg = {"role": "assistant", "content": response_message}
            self.chat_history.append(assistant_msg)
            self.prune_history()

            return self._make_answer(input_message, response_message)

        except Exception as e:
            logger.error(f"[GrokClient] {type(e).__name__}: {str(e)}")
            if self.chat_history and self.chat_history[-1].get("role") == "user":
                self.chat_history.pop()
            raise

    def prune_history(self) -> None:
        while len(self.chat_history) > self.MAX_HISTORY_LENGTH + 1:
            if len(self.chat_history) >= 3:
                self.chat_history.pop(1)
                if len(self.chat_history) > 2:
                    self.chat_history.pop(1)
            else:
                break
