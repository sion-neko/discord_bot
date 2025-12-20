import google.generativeai as genai
import os
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
genai.configure(api_key=GOOGLE_API_KEY)


class Gemini():
    def __init__(self):
        self.gemini_pro = genai.GenerativeModel("gemini-1.5-flash")
        self.zunda_chat = self.gemini_pro.start_chat(history=[])
        

    def question(self, msg):
        genai.configure(api_key=GOOGLE_API_KEY)
        try:
            response = self.gemini_pro.generate_content(msg, safety_settings=safety_config, generation_config=generation_config)
            return self._make_answer(msg, response.text)
        except Exception as e:
            print(e)
            return -1
    
    def char_talk(self, msg):
        genai.configure(api_key=GOOGLE_API_KEY)
        try:
            response = self.zunda_chat.send_message(msg, safety_settings=safety_config, generation_config=generation_config)
            if len(self.zunda_chat.history) > 20:
                a = self.zunda_chat.history.pop(2)
                b = self.zunda_chat.history.pop(2)
                self.gemini_pro.start_chat(history=self.zunda_chat.history)
                print("下記の会話を削除-character。")
                print("--------------")
                print(f"{a.role}:{a.parts[0].text}")
                print(f"{b.role}:{b.parts[0].text}")
                print("--------------")
            
            return self._make_answer(msg, response.text)
    
        except Exception as e:
            print(e)
            return -1
    
    def _make_answer(self, msg, response):
        answer = "> "+ msg + "\n\n" + response
        return answer
    
    def zunda_initialize(self):
        genai.configure(api_key=GOOGLE_API_KEY)
        self.zunda_chat = self.gemini_pro.start_chat(history=[])
        self.zunda_chat.send_message("あなたは、今からずんだもんです。ずんだもんは語尾に「のだ」や「なのだ」がつきます。\
                                     これから、あなた(ずんだもん)はいろいろ会話をすることになりますが、会話の返答は全て300文字以内で答えてあげてください。短い分には問題ありません。"\
                                     , safety_settings=safety_config, generation_config=generation_config)

