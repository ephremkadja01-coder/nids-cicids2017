from pydantic import BaseModel
from typing import Dict

class AgentRequest(BaseModel):
    prompt: str
    features: Dict[str, float]
    live_alerts: int = 0