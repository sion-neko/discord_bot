import os
from ai.clients import GroqClient, GeminiClient, PerplexityClient
from ai.exceptions import AIError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AIManager:
    """
    AI Client管理クラス (自動フォールバック機能付き)
    Groqを優先して試行し、エラー時にGeminiへフォールバック
    """

    def __init__(self):
        self.groq_client = None
        self.gemini_client = None
        self.perplexity_client = None

        clients_enabled = []

        # Groqクライアントを初期化 (API keyがある場合)
        if os.getenv('GROQ_API_KEY'):
            try:
                self.groq_client = GroqClient()
                clients_enabled.append("Groq")
            except Exception as e:
                logger.warning(f"Groq init failed: {e}")

        # Geminiクライアントを初期化 (フォールバック用・必須)
        if os.getenv('GOOGLE_API_KEY'):
            try:
                self.gemini_client = GeminiClient()
                clients_enabled.append("Gemini")
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")
                raise ValueError("Gemini APIは必須です (フォールバック用)")
        else:
            raise ValueError("GOOGLE_API_KEY は必須です (フォールバック用)")

        # Perplexityクライアントを初期化 (Web検索用・オプション)
        if os.getenv('PERPLEXITY_API_KEY'):
            try:
                self.perplexity_client = PerplexityClient()
                clients_enabled.append("Perplexity")
            except Exception as e:
                logger.warning(f"Perplexity init failed: {e}")
                self.perplexity_client = None

        # 少なくとも1つのクライアントが必要
        if not self.groq_client and not self.gemini_client:
            raise ValueError("利用可能なAI Clientがありません。APIキーを確認してください")

        logger.info(f"AI clients: {', '.join(clients_enabled)}")

    def send_message(self, message: str) -> str:
        """
        メッセージを送信 (自動フォールバック付き)

        Returns:
            str: 通常の会話応答

        Raises:
            AIError: 全てのAI Clientが失敗した場合
        """
        # Groqを優先して試行 (利用可能な場合)
        if self.groq_client is not None:
            try:
                return self.groq_client.send_message(message)
            except Exception as e:
                logger.warning(f"Groq failed, fallback to Gemini: {type(e).__name__}")

        # Geminiへフォールバック (初期化時に存在保証済み)
        try:
            return self.gemini_client.send_message(message)
        except Exception as e:
            error_msg = f"All APIs failed. Gemini: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            raise AIError(error_msg) from e
