import os
import requests
from typing import List, Dict


class GoogleSearchClient:
    """Google Custom Search APIクライアント"""

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('SEARCH_ENGINE_ID')

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY が環境変数に設定されていません")
        if not self.search_engine_id:
            raise ValueError("SEARCH_ENGINE_ID が環境変数に設定されていません")

        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Google Custom Search APIで検索

        Args:
            query: 検索クエリ
            num_results: 取得する結果の数 (最大10)

        Returns:
            [
                {
                    "title": "ページタイトル",
                    "link": "URL",
                    "snippet": "スニペット"
                },
                ...
            ]
        """
        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10),  # 最大10件
                'lr': 'lang_ja',  # 日本語優先
                'gl': 'jp'  # 日本の検索結果
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 検索結果を抽出
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', '')
                })

            print(f"[GoogleSearchClient] 検索成功: {len(results)}件取得")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[GoogleSearchClient] 検索失敗: {e}")
            raise
        except Exception as e:
            print(f"[GoogleSearchClient] エラー: {e}")
            raise
