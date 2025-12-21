import os
from ai.clients import GroqClient, GeminiClient


class AIManager:
    """
    AI Client管理クラス (自動フォールバック機能付き)
    Groqを優先して試行し、エラー時にGeminiへフォールバック
    """

    def __init__(self):
        self.groq_client = None
        self.gemini_client = None

        # Groqクライアントを初期化 (API keyがある場合)
        if os.getenv('GROQ_API_KEY'):
            try:
                self.groq_client = GroqClient()
                print("[AIManager] Groq client を初期化しました")
            except Exception as e:
                print(f"[AIManager] Groq初期化失敗: {e}")
        else:
            print("[AIManager] GROQ_API_KEY が未設定のため、Groqは無効です")

        # Geminiクライアントを初期化 (フォールバック用・必須)
        if os.getenv('GOOGLE_API_KEY'):
            try:
                self.gemini_client = GeminiClient()
                print("[AIManager] Gemini client を初期化しました")
            except Exception as e:
                print(f"[AIManager] Gemini初期化失敗: {e}")
                raise ValueError("Gemini APIは必須です (フォールバック用)")
        else:
            raise ValueError("GOOGLE_API_KEY は必須です (フォールバック用)")

        # 少なくとも1つのクライアントが必要
        if not self.groq_client and not self.gemini_client:
            raise ValueError("利用可能なAI Clientがありません。APIキーを確認してください")

    def send_message(self, message: str) -> str:
        """
        AIにメッセージを送信 (自動フォールバック付き)
        Groqを優先し、エラー時はGeminiへフォールバック
        """

        # Groqを優先して試行 (利用可能な場合)
        if self.groq_client is not None:
            try:
                response = self.groq_client.send_message(message)
                print(f"[AIManager] ✓ Groq API を使用しました")

                return response

            except Exception as e:
                print(f"[AIManager] Groq失敗 ({type(e).__name__}): {str(e)}")
                print(f"[AIManager] → Geminiへフォールバック中...")

        # Geminiへフォールバック (またはGroq無効時はGeminiを直接使用)
        try:
            response = self.gemini_client.send_message(message)

            if self.groq_client is None:
                print(f"[AIManager] ✓ Gemini API を使用しました (Groq無効)")
            else:
                print(f"[AIManager] ✓ Gemini API を使用しました (フォールバック)")

            return response

        except Exception as e:
            error_msg = f"[AIManager] 両方のAPIが失敗しました! Geminiエラー: {type(e).__name__}: {str(e)}"
            print(error_msg)
            return f"エラーが発生しました。両方のAPIが利用できません。\n技術詳細: {str(e)}"
