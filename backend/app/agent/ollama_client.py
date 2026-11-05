from groq import Groq

def call_ollama(prompt: str, model: str = "llama-3.3-70b-versatile") -> str:
    try:
        # ⚠️ COLLE TA CLÉ API GROQ ICI (elle commence par gsk_...)
        client = Groq(api_key="gsk_TA_CLE_API_ICI") 
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.3, # Un peu de créativité mais pas trop
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Erreur de l'API Groq : {str(e)}"