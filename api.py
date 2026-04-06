import requests
import json
from utils.logger import setup_logger

logger = setup_logger(__name__)


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
