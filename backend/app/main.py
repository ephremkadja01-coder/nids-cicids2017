from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import agent, live, predict, transcribe

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the NIDS API. Go to /docs for Swagger UI."}

@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": True}


app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(agent.router, prefix="/api/v1", tags=["Agent"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["Transcription"])
app.include_router(live.router, prefix="/api/v1", tags=["Live"])