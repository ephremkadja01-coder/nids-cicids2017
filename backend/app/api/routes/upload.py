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
        
        # On supprime la colonne Label si elle existe (pour ne pas la passer au modèle)
        if 'Label' in df.columns:
            df = df.drop(columns=['Label'])
        elif ' Label' in df.columns:
            df = df.drop(columns=[' Label'])

        results = []
        attack_count = 0
        
        # On prend 100 lignes au hasard
        sample_size = min(100, len(df))
        sample_df = df.sample(n=sample_size, random_state=42)
        
        for _, row in sample_df.iterrows():
            # On convertit tout en float proprement
            features = {str(k).strip(): float(v) for k, v in row.items()}
            
            res = pipeline.predict(features)
            results.append(res)
            if res["is_attack"]:
                attack_count += 1
                
        return {
            "status": "success",
            "total_analyzed": sample_size,
            "attacks_found": attack_count,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))