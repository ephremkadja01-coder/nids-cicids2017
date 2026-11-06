from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
from app.ml.pipeline import pipeline

router = APIRouter()

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        results = []
        # On analyse 5 lignes aléatoires pour faire rapide
        for _, row in df.sample(min(5, len(df))).iterrows():
            features = row.to_dict()
            # On nettoie les clés (souvent il y a des espaces dans les CSV)
            features = {str(k).strip(): float(v) for k, v in features.items() if str(v).replace('.','').isdigit()}
            
            res = pipeline.predict(features)
            results.append(res)
            
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))