import os
import requests
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)

BING_IMAGE_SEARCH_ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/search"


class API:

    def getInfo(self, url):
        try:
            session = requests.Session()
            response = session.get(url)
            response.raise_for_status()     # ステータスコード200番台以外は例外とする
        except requests.exceptions.RequestException as e:
            logger.error(f"[API] Request failed for {url}: {e}")
            return
        response.close()
        logger.debug(f"[API] GET {url} -> {response.status_code}")
        return response.json()

    def dog(self):
        url = "https://dog.ceo/api/breeds/image/random"
        response = self.getInfo(url)
        if (response):
            return response['message']
        else:
            logger.warning("[API] dog API: レスポンスが空です")
            return "取得できなかった"

    def image_search(self, query, count=1):
        api_key = os.getenv("BING_IMAGE_SEARCH_API_KEY")
        if not api_key:
            logger.warning("[API] BING_IMAGE_SEARCH_API_KEY が設定されていません")
            return None

        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {"q": query, "count": count, "safeSearch": "Moderate"}

        try:
            session = requests.Session()
            response = session.get(
                BING_IMAGE_SEARCH_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"[API] Bing Image Search failed for query={query}: {e}")
            return None
        response.close()
        logger.debug(
            f"[API] Bing Image Search {query} -> {response.status_code}")
        return response.json().get("value", [])
