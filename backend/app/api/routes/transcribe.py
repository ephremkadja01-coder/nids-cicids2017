from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    print(f"--- NOUVELLE REQUÊTE TRANSCRIPTION ---")
    print(f"Nom du fichier reçu : {file.filename}")
    print(f"Type de contenu : {file.content_type}")
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        audio_content = await file.read()
        
        print(f"Taille de l'audio : {len(audio_content)} octets")

        if len(audio_content) < 1000:
            print("⚠️ Fichier audio trop petit ou vide.")
            return {"text": ""}

        # Appel avec le modèle stable
        print("Envoi à Groq Whisper...")
        transcription = client.audio.transcriptions.create(
            file=(file.filename or "audio.webm", audio_content),
            model="whisper-large-v3", # On utilise le modèle stable
            response_format="text",
            language="fr"
        )
        
        print(f"Transcription réussie : {transcription}")
        return {"text": transcription.strip()}
        
    except Exception as e:
        print(f"❌ ERREUR SERVEUR : {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))