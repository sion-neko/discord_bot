import os
from openai import OpenAI
from ai.base_client import BaseAIClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

_TOOLS = [{"type": "web_search"}, {"type": "x_search"}]


class GrokClient(BaseAIClient):
    """xAI Grok API Client"""

    MODEL_NAME = "grok-3-mini"
    TEMPERATURE = 1.0
    MAX_TOKENS = 1000

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
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ] 

    def send_message(self, input_message: str) -> str:
        self.chat_history.append({"role": "user", "content": input_message})

        try:
            response = self.client.responses.create(
                model=self.MODEL_NAME,
                input=self.chat_history,
                tools=_TOOLS,
                temperature=self.TEMPERATURE,
                max_output_tokens=self.MAX_TOKENS,
            )

            response_message = response.output_text or "応答を生成できませんでした。"

            self.chat_history.append({"role": "assistant", "content": response_message})
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
