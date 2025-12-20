import requests
import json

class API:

    def getInfo(self,url):
        try:
            session = requests.Session()
            response = session.get(url)
            response.raise_for_status()     # ステータスコード200番台以外は例外とする
        except (requests.exceptions.RequestException,requests.exceptions.HTTPError):
            return
        response.close()
        return response.json()

    def dog(self):
        url = "https://dog.ceo/api/breeds/image/random"
        response = self.getInfo(url)
        if(response):
            return response['message']
        else:
            return "取得できなかった"
