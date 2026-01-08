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

        # Groqクライアントを初期化 (API keyがある場合)
        if os.getenv('GROQ_API_KEY'):
            try:
                self.groq_client = GroqClient()
                logger.info("[AIManager] Groq client を初期化しました")
            except Exception as e:
                logger.warning(f"[AIManager] Groq初期化失敗: {e}")
        else:
            logger.info("[AIManager] GROQ_API_KEY が未設定のため、Groqは無効です")

        # Geminiクライアントを初期化 (フォールバック用・必須)
        if os.getenv('GOOGLE_API_KEY'):
            try:
                self.gemini_client = GeminiClient()
                logger.info("[AIManager] Gemini client を初期化しました")
            except Exception as e:
                logger.error(f"[AIManager] Gemini初期化失敗: {e}")
                raise ValueError("Gemini APIは必須です (フォールバック用)")
        else:
            raise ValueError("GOOGLE_API_KEY は必須です (フォールバック用)")

        # Perplexityクライアントを初期化 (Web検索用・オプション)
        if os.getenv('PERPLEXITY_API_KEY'):
            try:
                self.perplexity_client = PerplexityClient()
                logger.info("[AIManager] Perplexity client を初期化しました")
            except Exception as e:
                logger.warning(f"[AIManager] Perplexity初期化失敗: {e}")
                self.perplexity_client = None
        else:
            logger.info("[AIManager] PERPLEXITY_API_KEY が未設定のため、Web検索は無効です")

        # 少なくとも1つのクライアントが必要
        if not self.groq_client and not self.gemini_client:
            raise ValueError("利用可能なAI Clientがありません。APIキーを確認してください")

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
                response = self.groq_client.send_message(message)
                logger.info(f"[AIManager] ✓ Groq API を使用しました")
                return response

            except Exception as e:
                logger.warning(f"[AIManager] Groq失敗 ({type(e).__name__}): {str(e)}")
                logger.info(f"[AIManager] → Geminiへフォールバック中...")

        # Geminiへフォールバック (初期化時に存在保証済み)
        try:
            response = self.gemini_client.send_message(message)

            if self.groq_client is None:
                logger.info(f"[AIManager] ✓ Gemini API を使用しました (Groq無効)")
            else:
                logger.info(f"[AIManager] ✓ Gemini API を使用しました (フォールバック)")

            return response

        except Exception as e:
            error_msg = f"両方のAPIが失敗しました。Geminiエラー: {type(e).__name__}: {str(e)}"
            logger.error(f"[AIManager] {error_msg}")
            raise AIError(error_msg) from e
