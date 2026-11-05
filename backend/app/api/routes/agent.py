from fastapi import APIRouter, HTTPException
import time

from app.schemas.agent import AgentRequest
from app.ml.pipeline import pipeline
from app.agent.prompts import get_soc_prompt
from app.agent.ollama_client import call_ollama

router = APIRouter()

@router.post("/agent")
def ask_agent(data: AgentRequest):
    try:
        # 1. Prédiction Machine Learning
        start_time = time.time()
        ml_result = pipeline.predict(data.features)
        inference_time_ms = (time.time() - start_time) * 1000
        
        # 2. Préparation du prompt
        prompt = get_soc_prompt(data.prompt, ml_result['probability'], ml_result['verdict'])
        
        # ⚠️ LA MAGIE EST ICI : On force l'IA à prendre en compte les alertes du flux Scapy
        if data.live_alerts > 0:
            prompt += f"\n\nATTENTION CRITIQUE : Le système de capture réseau (Scapy) a détecté {data.live_alerts} alertes d'attaque en temps réel sur le dashboard. Même si le flux analysé ci-dessus est BENIGN, tu DOIS impérativement mentionner ces {data.live_alerts} alertes actives à l'utilisateur et lui recommander une investigation immédiate."
        
        # 3. Appel au LLM
        agent_text = call_ollama(prompt)
        
        # 4. On renvoie tout au frontend
        return {
            "is_attack": ml_result["is_attack"],
            "probability": ml_result["probability"],
            "verdict": ml_result["verdict"],
            "agent_response": agent_text.strip(),
            "inference_time_ms": round(inference_time_ms, 2),
            "risk_score": int(ml_result['probability'] * 100),
            "active_alerts": 1 if ml_result['is_attack'] else 0,
            "trace": {
                "model_used": "openai/gpt-oss-120b (Groq)",
                "input_data": data.features,
                "ml_verdict": ml_result['verdict'],
                "ml_probability": f"{ml_result['probability'] * 100:.4f}%",
                "live_alerts_seen": data.live_alerts # <-- Ajouté pour la traçabilité
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))