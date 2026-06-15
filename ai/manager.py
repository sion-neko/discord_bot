import os
from ai.clients import GrokClient, PerplexityClient
from ai.exceptions import AIError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIManager:
    """AI Client管理クラス"""

    def __init__(self):
        self.grok_client = None
        self.perplexity_client = None

        clients_enabled = []

        api_key = os.getenv('XAI_API_KEY')
        if not api_key:
            raise ValueError("XAI_API_KEY は必須です")

        try:
            self.grok_client = GrokClient()
            clients_enabled.append("Grok")
        except Exception as e:
            logger.error(f"Grok init failed: {e}")
            raise

        if os.getenv('PERPLEXITY_API_KEY'):
            try:
                self.perplexity_client = PerplexityClient()
                clients_enabled.append("Perplexity")
            except Exception as e:
                logger.warning(f"Perplexity init failed: {e}")
                self.perplexity_client = None

        logger.info(f"AI clients: {', '.join(clients_enabled)}")

    def send_message(self, message: str, image_url: str = None) -> str:
        """
        Raises:
            AIError: API呼び出しが失敗した場合
        """
        try:
            return self.grok_client.send_message(message, image_url=image_url)
        except Exception as e:
            error_msg = f"Grok API failed. {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise AIError(error_msg) from e
