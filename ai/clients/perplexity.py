import os
from openai import OpenAI
from typing import Dict, List


class PerplexityClient:
    """Perplexity Sonar APIを使用したWeb検索クライアント"""

    MODEL_NAME = "sonar"

    def __init__(self):
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY が環境変数に設定されていません")

        # Perplexity APIはOpenAI互換
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )

    def search(self, query: str) -> Dict[str, any]:
        """
        Web検索を実行

        Args:
            query: 検索クエリ

        Returns:
            {
                "content": "要約テキスト",
                "citations": ["url1", "url2", ...]
            }
        """
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは正確な情報を提供する検索アシスタントです。日本語で簡潔に回答してください。"
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )

            content = response.choices[0].message.content

            # PerplexityのレスポンスからcitationsURLを抽出
            citations = []

            # 方法1: レスポンスオブジェクトのcitations属性
            if hasattr(response, 'citations') and response.citations:
                citations = response.citations

            # 方法2: メッセージレベルのcitations
            elif hasattr(response.choices[0].message, 'citations'):
                citations = response.choices[0].message.citations

            # 方法3: model_extra(拡張フィールド)からcitations取得
            elif hasattr(response, 'model_extra') and response.model_extra:
                citations = response.model_extra.get('citations', [])

            return {
                "content": content,
                "citations": citations
            }

        except Exception as e:
            print(f"[PerplexityClient] 検索失敗: {e}")
            raise
