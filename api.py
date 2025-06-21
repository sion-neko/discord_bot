import requests
import json # Not strictly necessary if only using response.json()

class API:
    """
    A class to interact with various external APIs.
    """
    def __init__(self):
        """
        Initializes the API class with a requests session for potential reuse.
        """
        self.session = requests.Session()

    def _get_info(self, url: str, params: dict = None) -> dict | None:
        """
        Private helper method to fetch JSON data from a URL.

        Args:
            url: The URL to fetch data from.
            params: Optional dictionary of URL parameters.

        Returns:
            A dictionary containing the JSON response, or None if an error occurs.
        """
        try:
            response = self.session.get(url, params=params, timeout=10) # Added timeout
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - URL: {url}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err} - URL: {url}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err} - URL: {url}")
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected error occurred during the request: {req_err} - URL: {url}")
        except json.JSONDecodeError as json_err:
            print(f"Failed to decode JSON response: {json_err} - URL: {url}")
        return None

    def dog(self) -> str:
        """
        Fetches a random dog image URL from the dog.ceo API.

        Returns:
            The URL of a random dog image, or an error message string.
        """
        url = "https://dog.ceo/api/breeds/image/random"
        response_data = self._get_info(url)
        if response_data and response_data.get("status") == "success":
            return response_data.get('message', "画像URLが見つかりませんでした。")
        return "犬の画像を取得できませんでした。" # More generic error

    def weather(self, api_key: str, city_name: str) -> str:
        """
        Fetches weather forecast data for a given city using OpenWeatherMap API.

        Args:
            api_key: Your OpenWeatherMap API key.
            city_name: The name of the city.

        Returns:
            A string containing the weather forecast, or an error message.
        """
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city_name, "appid": api_key, "lang": "ja"} # Added lang for Japanese
        response_data = self._get_info(url, params=params)

        if response_data and response_data.get("cod") == "200": # Check API specific success code
            result = f"{city_name}の天気予報：\n"
            for item in response_data.get("list", []):
                # Ensure necessary keys exist before accessing
                dt_txt = item.get("dt_txt", "不明な日時")
                weather_main = item.get("weather", [{}])[0].get('description', "不明な天気") # Use description for more detail
                result += f"{dt_txt}：{weather_main}\n"
            return result if response_data.get("list") else f"{city_name}の予報データがありません。"
        elif response_data and response_data.get("message"):
             return f"{city_name}の天気を取得できませんでした。エラー: {response_data.get('message')}"
        return f"{city_name}の天気を取得できませんでした。"

    def wiki(self, search_term: str, summary_sentences: int = 1) -> str:
        """
        Fetches a summary from Japanese Wikipedia for a given search term.

        Args:
            search_term: The term to search for on Wikipedia.
            summary_sentences: The number of sentences for the summary (approximate).

        Returns:
            A summary from Wikipedia, or an error message.
        """
        url = "https://ja.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            # "exsentences": summary_sentences, # exsentences might be better for summaries
            "exintro": True, # exintro provides the introductory section
            "titles": search_term,
            "format": "json"
        }
        response_data = self._get_info(url, params=params)

        if response_data:
            pages = response_data.get('query', {}).get('pages', {})
            if not pages:
                return f"「{search_term}」に関する情報は見つかりませんでした。"

            page_id = next(iter(pages), None)
            if page_id == "-1": # Page does not exist
                 return f"「{search_term}」というタイトルのページは存在しません。"
            
            if page_id:
                document = pages[page_id].get("extract", "")
                if document:
                    # A simple way to get the first part if exsentences/exintro doesn't give desired length
                    # For more precise sentence splitting, a library might be needed.
                    target = '\n\n' if summary_sentences > 1 else '\n' # This logic might need adjustment
                    idx = document.find(target)
                    result = document[:idx] if idx != -1 else document
                    return result.strip() if result.strip() else f"「{search_term}」の要約を取得できませんでした。"
                return f"「{search_term}」の本文が見つかりません。"
        return f"「{search_term}」という言葉をWikipediaで検索できませんでした。"

    def address(self, zipcode: str) -> str:
        """
        Fetches the full address for a given Japanese zipcode.

        Args:
            zipcode: The Japanese zipcode (e.g., "1000000").

        Returns:
            The full address, or an error message.
        """
        url = f'https://api.zipaddress.net/' # No .format needed with f-string
        params = {'zipcode': zipcode}
        response_data = self._get_info(url, params=params)

        if response_data and response_data.get('code') == 200: # Check API specific success code
            try:
                return response_data['data']['fullAddress']
            except KeyError:
                return f"{zipcode}という郵便番号に対応する住所は見つかりませんでした。"
        elif response_data and response_data.get('message'):
            return f"郵便番号{zipcode}の情報を取得できませんでした。エラー: {response_data.get('message')}"
        return f"{zipcode}という郵便番号は存在しないか、検索できませんでした。"

    def apex(self, api_key: str, player_name: str, platform: str = "origin") -> str:
        """
        Fetches Apex Legends player stats from tracker.gg API.

        Args:
            api_key: Your TRN-Api-Key for tracker.gg.
            player_name: The player's username.
            platform: The player's platform (e.g., "origin", "psn", "xbl").

        Returns:
            A string containing player stats, or an error message.
        """
        base_url = "https://public-api.tracker.gg/v2/apex/standard/"
        endpoint = f"profile/{platform}/{player_name}"
        # Parameters should be passed to _get_info, headers are handled by session or direct get
        headers = {"TRN-Api-Key": api_key}
        
        try:
            # For APIs requiring headers, requests.get needs them directly or session.headers.update
            # self.session.headers.update(headers) # Option 1: Update session headers
            # response_data = self._get_info(base_url + endpoint)
            # self.session.headers.clear() # And clear after if they are not always needed

            # Option 2: Pass headers directly (if _get_info is modified to accept headers)
            # For now, let's make a direct call as _get_info doesn't support custom headers for one call
            response = self.session.get(base_url + endpoint, headers=headers, timeout=15)
            response.raise_for_status()
            response_data = response.json()

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred for Apex API: {http_err}")
            if http_err.response.status_code == 401:
                return "Apex APIキーが無効か、認証に失敗しました。"
            elif http_err.response.status_code == 404:
                return f"プレイヤー「{player_name}」({platform})が見つかりませんでした。"
            return f"Apex APIでエラーが発生しました: {http_err.response.status_code}"
        except requests.exceptions.RequestException as req_err:
            print(f"Request error for Apex API: {req_err}")
            return f"Apex APIへの接続中にエラーが発生しました: {req_err}"
        except json.JSONDecodeError as json_err:
            print(f"Failed to decode JSON from Apex API: {json_err}")
            return "Apex APIからの応答を解析できませんでした。"

        if response_data and "data" in response_data:
            result = f"--- {player_name} ({platform}) の戦績 ---\n"
            stats = response_data['data'].get('segments', [{}])[0].get('stats', {})
            if not stats:
                return f"プレイヤー「{player_name}」の統計データが見つかりません。"

            for key, value_data in stats.items():
                if isinstance(value_data, dict): # Ensure value_data is a dictionary
                    rank_name = value_data.get('metadata', {}).get('rankName')
                    display_value = value_data.get('displayValue')
                    if rank_name:
                        result += f"{value_data.get('displayName', key)}：{rank_name}\n"
                    elif display_value:
                        result += f"{value_data.get('displayName', key)}：{display_value}\n"
                    else:
                        result += f"{value_data.get('displayName', key)}：データなし\n"
            result += "---------------------------------" # Consistent length
            return result
        elif response_data and "errors" in response_data:
            error_message = response_data["errors"][0].get("message", "不明なエラー")
            return f"プレイヤー「{player_name}」の検索中にエラーが発生しました: {error_message}"

        return f"プレイヤー「{player_name}」({platform})の情報を見つけられませんでした。"

# Example usage (for testing purposes):
# if __name__ == "__main__":
#     api_client = API()
    # print(api_client.dog())
    # print(api_client.weather("YOUR_OPENWEATHERMAP_API_KEY", "Tokyo"))
    # print(api_client.wiki("Pythonプログラミング言語"))
    # print(api_client.wiki("存在しない可能性が高いページ名"))
    # print(api_client.address("1000000"))
    # print(api_client.address("9999999")) # Test invalid zipcode
    # print(api_client.apex("YOUR_TRN_API_KEY", "some_player_name", "origin"))