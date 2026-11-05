from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import predict

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

# Inclure la route de prédiction
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the NIDS API. Go to /docs for Swagger UI."}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": True}