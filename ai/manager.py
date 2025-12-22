import os
from ai.clients import GroqClient, GeminiClient, PerplexityClient
from search import GoogleSearchClient


class AIManager:
    """
    AI Client管理クラス (自動フォールバック機能付き)
    Groqを優先して試行し、エラー時にGeminiへフォールバック
    """

    def __init__(self):
        self.groq_client = None
        self.gemini_client = None
        self.perplexity_client = None
        self.google_search_client = None

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

        # Perplexityクライアントを初期化 (Web検索用・オプション)
        if os.getenv('PERPLEXITY_API_KEY'):
            try:
                self.perplexity_client = PerplexityClient()
                print("[AIManager] Perplexity client を初期化しました")
            except Exception as e:
                print(f"[AIManager] Perplexity初期化失敗: {e}")
                self.perplexity_client = None
        else:
            print("[AIManager] PERPLEXITY_API_KEY が未設定のため、Web検索は無効です")

        # Google Search初期化 (Web検索用・オプション)
        if os.getenv('GOOGLE_SEARCH_API_KEY') and os.getenv('SEARCH_ENGINE_ID'):
            try:
                self.google_search_client = GoogleSearchClient()
                print("[AIManager] Google Search client を初期化しました")
            except Exception as e:
                print(f"[AIManager] Google Search初期化失敗: {e}")
                self.google_search_client = None
        else:
            print("[AIManager] GOOGLE_SEARCH_API_KEY/SEARCH_ENGINE_ID が未設定のため、Google検索は無効です")

        # 少なくとも1つのクライアントが必要
        if not self.groq_client and not self.gemini_client:
            raise ValueError("利用可能なAI Clientがありません。APIキーを確認してください")

    def send_message(self, message: str) -> str | dict:
        """
        メッセージを送信 (自動フォールバック付き)

        Returns:
            str: 通常の会話応答
            dict: 検索結果 {"type": "search_result", "summary": "...", "citations": [...], "query": "..."}
                  またはエラー {"type": "error", "message": "..."}
        """
        response = None

        # Groqを優先して試行 (利用可能な場合)
        if self.groq_client is not None:
            try:
                response = self.groq_client.send_message(message)

                # Tool call要求かチェック
                if isinstance(response, dict) and response.get("tool") == "web_search":
                    return self._execute_search(response["query"])

                print(f"[AIManager] ✓ Groq API を使用しました")
                return response

            except Exception as e:
                print(f"[AIManager] Groq失敗 ({type(e).__name__}): {str(e)}")
                print(f"[AIManager] → Geminiへフォールバック中...")

        # Geminiへフォールバック (またはGroq無効時はGeminiを直接使用)
        if self.gemini_client and response is None:
            try:
                response = self.gemini_client.send_message(message)

                # Geminiも同様にTool callをチェック (将来的に実装する場合)
                if isinstance(response, dict) and response.get("tool") == "web_search":
                    return self._execute_search(response["query"])

                if self.groq_client is None:
                    print(f"[AIManager] ✓ Gemini API を使用しました (Groq無効)")
                else:
                    print(f"[AIManager] ✓ Gemini API を使用しました (フォールバック)")

                return response

            except Exception as e:
                error_msg = f"[AIManager] 両方のAPIが失敗しました! Geminiエラー: {type(e).__name__}: {str(e)}"
                print(error_msg)
                return f"エラーが発生しました。両方のAPIが利用できません。\n技術詳細: {str(e)}"

        return response or "エラーが発生しました。"

    def _execute_search(self, query: str) -> dict:
        """
        Google検索を実行してGroqに要約させる

        Args:
            query: 検索クエリ

        Returns:
            検索結果辞書 または エラー辞書
        """
        if not self.google_search_client:
            return {
                "type": "error",
                "message": "Web検索機能は現在利用できません。GOOGLE_SEARCH_API_KEY/SEARCH_ENGINE_IDが設定されていません。"
            }

        try:
            print(f"[AIManager] Google検索実行: {query}")
            search_results = self.google_search_client.search(query, num_results=5)

            if not search_results:
                return {
                    "type": "error",
                    "message": "検索結果が見つかりませんでした。"
                }

            # 検索結果をGroqに渡して要約させる
            summary = self._summarize_with_groq(query, search_results)

            # URLリストを抽出
            citations = [result['link'] for result in search_results]

            return {
                "type": "search_result",
                "summary": summary,
                "citations": citations,
                "query": query
            }

        except Exception as e:
            print(f"[AIManager] Google検索失敗: {e}")
            return {
                "type": "error",
                "message": f"検索中にエラーが発生しました: {str(e)}"
            }

    def _summarize_with_groq(self, query: str, search_results: list) -> str:
        """
        検索結果をGroqに渡して要約

        Args:
            query: 検索クエリ
            search_results: Google検索結果

        Returns:
            要約テキスト
        """
        # 検索結果を整形
        results_text = "\n\n".join([
            f"【{i+1}】 {result['title']}\n{result['snippet']}\nURL: {result['link']}"
            for i, result in enumerate(search_results)
        ])

        # Groqに要約を依頼
        prompt = f"""以下のWeb検索結果を基に、ユーザーの質問「{query}」に対して、日本語で簡潔に回答してください。

検索結果:
{results_text}

回答は以下の形式で:
1. 質問に対する明確な回答
2. 重要なポイントを箇条書きで
3. 簡潔に(200文字程度)
"""

        if self.groq_client:
            try:
                # 一時的な履歴を作成(通常の会話履歴に影響させない)
                temp_messages = [{"role": "user", "content": prompt}]

                response = self.groq_client.client.chat.completions.create(
                    model=self.groq_client.MODEL_NAME,
                    messages=temp_messages,
                    temperature=0.3,  # 事実ベースなので低めに
                    max_tokens=500
                )

                return response.choices[0].message.content or "要約を生成できませんでした。"

            except Exception as e:
                print(f"[AIManager] Groq要約失敗: {e}")
                # フォールバック: 最初の検索結果のスニペットを返す
                return search_results[0]['snippet']

        # Groqが使えない場合は最初の検索結果を返す
        return search_results[0]['snippet']
