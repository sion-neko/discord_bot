import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv
safety_config = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]

generation_config = genai.types.GenerationConfig(
        candidate_count=1,
        max_output_tokens=1000,
        temperature=1.0)
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# GOOGLE_API_KEYの確認
if not GOOGLE_API_KEY:
    print("ERROR: GOOGLE_API_KEYが設定されていません。.envファイルを確認してください。")
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)


class Gemini():
    def __init__(self):
        self.gemini_pro = genai.GenerativeModel("gemini-flash-latest")
        self.zunda_chat = self.gemini_pro.start_chat(history=[])
        

    def question(self, msg):
        try:
            response = self.gemini_pro.generate_content(msg, safety_settings=safety_config, generation_config=generation_config)
            return self._make_answer(msg, response.text)
        except Exception as e:
            error_message = f"ERROR in question(): {type(e).__name__}: {str(e)}"
            print(error_message)
            return f"エラーが発生しました: {str(e)}"
    
    def char_talk(self, msg):
        try:
            response = self.zunda_chat.send_message(msg, safety_settings=safety_config, generation_config=generation_config)
            if len(self.zunda_chat.history) > 20:
                # 古い会話履歴を削除（システムプロンプトを保持して、その次の会話ペアを削除）
                removed_messages = []
                if len(self.zunda_chat.history) >= 4:
                    # インデックス2と3（システムプロンプト後の最初の会話ペア）を削除
                    removed_messages.append(self.zunda_chat.history.pop(2))
                    removed_messages.append(self.zunda_chat.history.pop(2))
                    self.zunda_chat = self.gemini_pro.start_chat(history=self.zunda_chat.history)
                    print("下記の会話を削除-character。")
                    print("--------------")
                    for msg_item in removed_messages:
                        print(f"{msg_item.role}:{msg_item.parts[0].text}")
                    print("--------------")
            
            return self._make_answer(msg, response.text)

        except Exception as e:
            error_message = f"ERROR in char_talk(): {type(e).__name__}: {str(e)}"
            print(error_message)
            return f"エラーが発生しました: {str(e)}"
    
    def _make_answer(self, msg, response):
        answer = "> "+ msg + "\n\n" + response
        return answer
    
    def zunda_initialize(self):
        self.zunda_chat = self.gemini_pro.start_chat(history=[])
        self.zunda_chat.send_message("あなたは、今からずんだもんです。ずんだもんは語尾に「のだ」や「なのだ」がつきます。\
                                     これから、あなた(ずんだもん)はいろいろ会話をすることになりますが、会話の返答は全て300文字以内で答えてあげてください。短い分には問題ありません。"\
                                     , safety_settings=safety_config, generation_config=generation_config)

