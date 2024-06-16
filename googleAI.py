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
        stop_sequences=['x'],
        max_output_tokens=1000,
        temperature=1.0)
load_dotenv() 
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)


class Gemini():
    def __init__(self):
        self.gemini_pro = genai.GenerativeModel("gemini-1.5-pro")
        self.chat = self.gemini_pro.start_chat(history=[])
        

    def question(self, msg):
        genai.configure(api_key=GOOGLE_API_KEY)
        try:
            response = self.gemini_pro.generate_content(msg, safety_settings=safety_config, generation_config=generation_config)
            return self._make_answer(msg, response.text)
        except Exception as e:
            print(e)
            return -1
        
    
    def talk(self, msg):
        genai.configure(api_key=GOOGLE_API_KEY)
        try:
            response = self.chat.send_message(msg, safety_settings=safety_config, generation_config=generation_config)
            if len(self.chat.history) > 20:
                a = self.chat.history.pop(2)
                b = self.chat.history.pop(2)
                self.gemini_pro.start_chat(history=self.chat.history)
                print("下記の会話を削除。")
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
    
    def _initialize_talk(self):
        genai.configure(api_key=GOOGLE_API_KEY)
        self.chat = self.gemini_pro.start_chat(history=[])
        self.chat.send_message("あなたは、今からムスカ大佐です。ムスカ大佐の情報を記載するのでムスカ大佐のように振る舞ってください。\
        ムスカ大佐の情報：\
        本名は「ロムスカ・パロ・ウル・ラピュタ」。\
        次のセリフで有名です。\
        「３分間待ってやる」「時間だ。答えを聞こう」「私をあまり怒らせないほうがいいぞ」「目がぁぁー！目がぁぁぁぁぁぁぁー！！」「見ろ!人がゴミのようだ!」\
        「目がぁぁー！目がぁぁぁぁぁぁぁー！！」は「バルス」というセリフに対して用いられます。\
        これから、あなた(ムスカ大佐)に質問が来ますが、質問には300文字以内で答えてください。", safety_settings=safety_config, generation_config=generation_config)

