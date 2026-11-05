import requests

def call_ollama(prompt: str, model: str = "mistral") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=15
        )
        response.raise_for_status()
        return response.json().get("response", "Erreur de génération.")
    except requests.exceptions.ConnectionError:
        return "Erreur : Ollama n'est pas lancé. Lancez 'ollama run mistral' dans un terminal."
    except Exception as e:
        return f"Erreur inattendue : {str(e)}"