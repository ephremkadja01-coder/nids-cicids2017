from fastapi import APIRouter, HTTPException
from app.schemas.prediction import NetworkFlowInput, PredictionResponse
from app.ml.pipeline import pipeline

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
def predict_network_flow(data: NetworkFlowInput):
    try:
        result = pipeline.predict(data.features)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))