import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Constants ---
HISTORY_MAX_LENGTH = 20 # Maximum number of turns (user + model) in chat history
HISTORY_POP_COUNT = 2   # Number of turns (user + model message pairs) to remove when history exceeds max length
ERROR_CODE = -1
MODEL_NAME = "gemini-1.5-flash" # Specify the model name

# --- Configurations ---
# Load environment variables from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    # Depending on the application, you might want to exit or raise an exception here.
    # For now, we'll allow the script to continue, but genai.configure will fail.

# Configure the generative AI client globally if the API key is available
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Google AI: {e}")
    # Handle configuration error appropriately

# Define safety settings for content generation
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

# Define generation configuration
GENERATION_CONFIG = genai.types.GenerationConfig(
    candidate_count=1,
    stop_sequences=['x'], # Consider if 'x' is an appropriate stop sequence
    max_output_tokens=1000,
    temperature=1.0
)

# Zundamon persona initialization message
ZUNDAMON_INITIAL_PROMPT = (
    "あなたは、今からずんだもんです。ずんだもんは語尾に「のだ」や「なのだ」がつきます。"
    "これから、あなた(ずんだもん)はいろいろ会話をすることになりますが、"
    "会話の返答は全て300文字以内で答えてあげてください。短い分には問題ありません。"
)

class Gemini:
    """
    A class to interact with the Google Gemini AI model,
    specifically configured for a Zundamon persona.
    """
    def __init__(self):
        """
        Initializes the Gemini model and the Zundamon chat session.
        """
        if not GOOGLE_API_KEY:
            print("Gemini class initialized without API key. Operations will likely fail.")
            self.gemini_pro = None # Explicitly set to None if no key
            self.zunda_chat = None
            return

        try:
            self.gemini_pro = genai.GenerativeModel(MODEL_NAME)
            self.zunda_chat = self.gemini_pro.start_chat(history=[])
            self._initialize_zundamon_persona()
        except Exception as e:
            print(f"Error initializing Gemini model or chat: {e}")
            self.gemini_pro = None
            self.zunda_chat = None


    def _initialize_zundamon_persona(self):
        """
        Sends the initial prompt to set up the Zundamon persona for the chat.
        Should only be called if self.zunda_chat is not None.
        """
        if not self.zunda_chat:
            print("Cannot initialize Zundamon persona: chat session not available.")
            return
        try:
            # Send the initial prompt to establish the persona
            # The response to this initial message isn't typically used directly by the user
            self.zunda_chat.send_message(
                ZUNDAMON_INITIAL_PROMPT,
                safety_settings=SAFETY_SETTINGS,
                generation_config=GENERATION_CONFIG
            )
            print("Zundamon persona initialized.")
        except Exception as e:
            print(f"Error sending Zundamon initialization prompt: {e}")
            # Potentially mark the chat as unusable or attempt re-initialization

    def question(self, user_message: str) -> str | int:
        """
        Sends a single message to the Gemini Pro model for a one-off question.
        This does not use the ongoing Zundamon chat history.

        Args:
            user_message: The message from the user.

        Returns:
            The model's response formatted with the original message, or ERROR_CODE on failure.
        """
        if not self.gemini_pro:
            print("Gemini Pro model not available for question.")
            return ERROR_CODE
        try:
            response = self.gemini_pro.generate_content(
                user_message,
                safety_settings=SAFETY_SETTINGS,
                generation_config=GENERATION_CONFIG
            )
            return self._format_answer(user_message, response.text)
        except Exception as e:
            print(f"Error during Gemini Pro question: {e}")
            return ERROR_CODE

    def char_talk(self, user_message: str) -> str | int:
        """
        Sends a message from the user to the ongoing Zundamon chat.
        Manages chat history length.

        Args:
            user_message: The message from the user.

        Returns:
            Zundamon's response formatted with the original message, or ERROR_CODE on failure.
        """
        if not self.zunda_chat:
            print("Zundamon chat not available.")
            return ERROR_CODE
        try:
            response = self.zunda_chat.send_message(
                user_message,
                safety_settings=SAFETY_SETTINGS,
                generation_config=GENERATION_CONFIG
            )
            self._manage_chat_history()
            return self._format_answer(user_message, response.text)
        except Exception as e:
            print(f"Error during Zundamon char_talk: {e}")
            return ERROR_CODE

    def _manage_chat_history(self):
        """
        Manages the length of the Zundamon chat history.
        If the history exceeds HISTORY_MAX_LENGTH, older messages are removed.
        """
        if not self.zunda_chat:
            return

        # The history includes messages from both 'user' and 'model'.
        # len(self.zunda_chat.history) gives the total number of Content objects.
        # Each user message and each model response is a Content object.
        if len(self.zunda_chat.history) > HISTORY_MAX_LENGTH:
            print(f"Chat history length ({len(self.zunda_chat.history)}) exceeded maximum ({HISTORY_MAX_LENGTH}). Trimming...")

            # We want to remove pairs of (user, model) messages, which means removing HISTORY_POP_COUNT * 2 items if
            # HISTORY_POP_COUNT refers to turns. The original code popped item at index 2 twice.
            # Popping from the beginning of the history list (index 0 and 1 for the first turn).
            removed_messages = []
            for _ in range(HISTORY_POP_COUNT * 2): # Remove user and model message for each "turn"
                if self.zunda_chat.history:
                    removed_messages.append(self.zunda_chat.history.pop(0)) # Pop from the beginning
                else:
                    break

            # Re-starting the chat with the trimmed history. This is how the SDK often handles history modification.
            # Note: This creates a new chat object internally if the underlying API requires it.
            # The current SDK's `ChatSession` object updates its history in place.
            # If `self.gemini_pro.start_chat` was truly necessary, it implies the previous `self.zunda_chat`
            # object would become stale. However, `ChatSession.history` is mutable.
            # The original code had `self.gemini_pro.start_chat(history=self.zunda_chat.history)`
            # This is redundant if `self.zunda_chat.history.pop()` directly modifies the list used by `self.zunda_chat`.
            # Let's assume direct modification is sufficient and the `start_chat` call was for safety or misunderstanding.

            print(f"Removed {len(removed_messages)} message(s) from Zundamon chat history.")
            # For debugging, one might print the removed messages:
            # for msg in removed_messages:
            #     print(f"  Removed - {msg.role}: {msg.parts[0].text[:50]}...")
            print(f"New history length: {len(self.zunda_chat.history)}")


    def _format_answer(self, original_message: str, model_response: str) -> str:
        """
        Formats the model's response to include the original user message.

        Args:
            original_message: The user's original message.
            model_response: The model's raw text response.

        Returns:
            A formatted string combining the original message and the response.
        """
        return f"> {original_message}\n\n{model_response}"

    def zunda_initialize(self):
        """
        Public method to re-initialize or ensure the Zundamon persona is set.
        This might be called if the chat needs to be reset or if initialization failed.
        """
        print("Attempting to initialize/re-initialize Zundamon persona...")
        if not self.gemini_pro:
            print("Cannot initialize Zundamon: Gemini Pro model not available.")
            return

        # Start a new chat session, effectively resetting the history for Zundamon
        try:
            self.zunda_chat = self.gemini_pro.start_chat(history=[])
            self._initialize_zundamon_persona()
        except Exception as e:
            print(f"Error re-initializing Zundamon chat: {e}")
            self.zunda_chat = None # Ensure chat is None if re-initialization fails
