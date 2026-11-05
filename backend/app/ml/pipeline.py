import os
import json
import joblib
import pandas as pd
import numpy as np

# Calcul du chemin pour remonter à la racine du projet et trouver ml/models/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # backend/app/ml
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))) # racine
MODELS_DIR = os.path.join(ROOT_DIR, "ml", "models")

class NIDSPipeline:
    def __init__(self):
        # Chargement des modèles
        self.xgb_model = joblib.load(os.path.join(MODELS_DIR, "xgb_nids.joblib"))
        
        # Chargement des métadonnées
        with open(os.path.join(MODELS_DIR, "metadata.json"), "r") as f:
            self.metadata = json.load(f)
            
        self.features = self.metadata["features"]
        self.threshold = self.metadata["optimal_threshold_xgb"]

    def predict(self, input_features: dict):
        df = pd.DataFrame([input_features])
        
        # Remplir les features manquantes avec 0
        for f in self.features:
            if f not in df.columns:
                df[f] = 0.0
                
        # Garder uniquement les features attendues dans le bon ordre
        df = df[self.features]
        
        # Prédiction
        proba = float(self.xgb_model.predict_proba(df)[0, 1])
        is_attack = proba >= self.threshold
        
        return {
            "is_attack": is_attack,
            "probability": proba,
            "threshold_used": self.threshold,
            "verdict": "ATTACK DETECTED" if is_attack else "BENIGN"
        }

# Instance globale
pipeline = NIDSPipeline()