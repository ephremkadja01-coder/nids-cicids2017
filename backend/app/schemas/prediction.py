from pydantic import BaseModel
from typing import Dict

class NetworkFlowInput(BaseModel):
    features: Dict[str, float]

class PredictionResponse(BaseModel):
    is_attack: bool
    probability: float
    threshold_used: float
    verdict: str