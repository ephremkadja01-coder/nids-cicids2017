import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def call_ollama(prompt: str, model: str = "openai/gpt-oss-120b") -> str:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3, # Un peu de créativité mais pas trop
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Erreur de l'API Groq : {str(e)}"