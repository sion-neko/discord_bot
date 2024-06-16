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

    def weather(self,APIkey,arg):
        url="http://api.openweathermap.org/data/2.5/forecast"
        params="?q="+arg+"&appid="+APIkey
        response = self.getInfo(url+params)
        result = ''
        if(response):
            for i in response["list"]:
                result += i["dt_txt"]+"、"+i["weather"][0]['main'] + "\n"
            return result
        else:
            return arg+"の天気を取得できませんでした。"

    def wiki(self,*arg):
        url = "https://ja.wikipedia.org/w/api.php"
        params="?action=query&prop=extracts&explaintext=+True+&exsectopnformat=plain&titles="+arg[0]+"&format=json"
        response = self.getInfo(url+params)
        if(response):
            pages = response['query']['pages']
            page_id = next(iter(pages))
            document = pages[page_id]["extract"]
            target = ''
            if(len(arg)==1):
                target = '\n'
            else:
                target = '\n\n'
            
            idx = document.find(target)
            result = document[:idx]
            if(result):
                return result
            return "'"+arg[0]+"'なんて言葉は知りません。"
        else:
            return "'"+arg[0]+"'という言葉を存じ上げません。"
        
    def address(self,arg):
        url = 'https://api.zipaddress.net/?zipcode={}'.format(arg)
        response = self.getInfo(url)
        if(response):
            try:
                result = response['data']['fullAddress']
            except KeyError:
                return str(arg)+"という郵便番号は存在しません。"
            return result
        else:
            return arg+"という郵便番号は存在しません。"

    
    def apex(self,APIkey,arg):
        base_url = "https://public-api.tracker.gg/v2/apex/standard/"
        params = "?TRN-Api-Key="+APIkey
        endpoint = "profile/origin/{}".format(arg)
        response = self.getInfo(base_url+endpoint+params)

        if(response):
            result = "---" + arg + "の戦績---\n"
            pas = response ['data']['segments'][0]['stats']
            for key, value in pas.items():
                try:
                    result += key + "：" + value['metadata']['rankName'] + "\n"
                except KeyError:
                    result += key + "：" + value['displayValue'] + "\n"
            result += "-----------"
            return result
        else:
            return "プレイヤー"+arg+"を見つけられませんでした。"
        


# test = API()
# print(test.address("a"))