from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
import os
from dotenv import load_dotenv

# On charge explicitement le .env ici
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    print(f"--- NOUVELLE REQUÊTE TRANSCRIPTION ---")
    print(f"Nom du fichier : {file.filename}")
    
    if not GROQ_API_KEY:
        print("❌ ERREUR : La clé GROQ_API_KEY est introuvable dans le .env")
        raise HTTPException(status_code=500, detail="Clé API manquante")

    try:
        client = Groq(api_key=GROQ_API_KEY)
        audio_content = await file.read()
        
        print(f"Taille de l'audio reçu : {len(audio_content)} octets")

        # Utilisation du modèle stable
        transcription = client.audio.transcriptions.create(
            file=(file.filename or "audio.webm", audio_content),
            model="whisper-large-v3", # Modèle stable
            response_format="text",
            language="fr"
        )
        
        print(f"✅ Transcription réussie : {transcription}")
        return {"text": transcription.strip()}
        
    except Exception as e:
        print(f"❌ ERREUR GROQ : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))