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
        
        # 2. Préparation du prompt pour Ollama
        prompt = get_soc_prompt(data.prompt, ml_result['probability'], ml_result['verdict'])
        
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
            "active_alerts": 1 if ml_result['is_attack'] else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))