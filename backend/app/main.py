import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import agent, live, predict, transcribe, upload
from app.ml.live_capture import run_sniffer_in_background
from groq import Groq
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

app = FastAPI(
    title="NIDS CICIDS2017 API",
    description="API for Network Intrusion Detection System (SOC Assistant)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def test_groq_connection():
    """Teste si la clé API Groq est valide au démarrage (hors CI)"""
    if os.environ.get("CI") == "true":
        return

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ ERREUR FATALE : GROQ_API_KEY est introuvable dans le fichier .env")
        return
    
    try:
        client = Groq(api_key=api_key)
        client.chat.completions.create(
            messages=[{"role": "user", "content": "ping"}],
            model="openai/gpt-oss-120b",
            max_tokens=1
        )
        print("✅ CONNEXION GROQ : La clé API est valide et opérationnelle !")
    except Exception as e:
        print(f"❌ ERREUR CONNEXION GROQ : {e}")

@app.on_event("startup")
def startup_event():
    print("🚀 Démarrage de l'API NIDS...")
    
    # 1. Test de la clé Groq
    test_groq_connection()

    # 2. Lancement de Scapy UNIQUEMENT en local (pas sur GitHub Actions)
    if os.environ.get("CI") != "true":
        run_sniffer_in_background()
    else:
        print("ℹ️ Mode CI détecté : le sniffer Scapy est désactivé pour éviter les erreurs réseau.")

@app.get("/")
def read_root():
    return {"message": "Welcome to the NIDS API. Go to /docs for Swagger UI."}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": True}

# --- ROUTES ---
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(agent.router, prefix="/api/v1", tags=["Agent"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["Transcription"])
app.include_router(live.router, prefix="/api/v1", tags=["Live"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])