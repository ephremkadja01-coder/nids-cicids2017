from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict
from app.ml.pipeline import pipeline

router = APIRouter()

# Liste des clients connectés (ton interface React)
active_connections = []

@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # On garde la connexion ouverte
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

class LivePacket(BaseModel):
    features: Dict[str, float]

@router.post("/predict-live")
async def predict_live(data: LivePacket):
    # 1. Prédiction rapide XGBoost
    ml_result = pipeline.predict(data.features)
    
    # 2. Création du payload à envoyer à React
    payload = {
        "is_attack": ml_result["is_attack"],
        "probability": ml_result["probability"],
        "verdict": ml_result["verdict"],
        "active_alerts": 1 if ml_result["is_attack"] else 0,
        "port": int(data.features.get("Destination Port", 0))
    }
    
    # 3. Diffusion en temps réel à tous les clients connectés
    for connection in active_connections:
        await connection.send_json(payload)
        
    return {"status": "packet_analyzed"}

@router.get("/trigger-fake-alert")
async def trigger_fake_alert():
    # On fabrique une fausse alerte d'attaque (sans passer par XGBoost)
    payload = {
        "is_attack": True,
        "probability": 0.99,
        "verdict": "ATTACK DETECTED",
        "active_alerts": 1,
        "port": 8080
    }

    # On l'envoie à tous les clients connectés (ton interface React)
    for connection in active_connections:
        await connection.send_json(payload)

    return {"message": "Fausse alerte envoyée !"}