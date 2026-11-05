from fastapi import APIRouter, UploadFile, File, HTTPException
from groq import Groq
import os

router = APIRouter()

# ⚠️ Utilise la même clé API que pour ton LLM
GROQ_API_KEY = "gsk_TA_CLE_API_ICI"

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # Lire le contenu du fichier audio envoyé par React
        audio_content = await file.read()
        
        # Envoyer à Groq Whisper (modèle ultra-rapide)
        transcription = client.audio.transcriptions.create(
            file=(file.filename, audio_content),
            model="whisper-large-v3",
            response_format="text",
            language="fr" # On force le français
        )
        
        return {"text": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))