"""
Production script for the NIDS ML Pipeline.
Automates CRISP-DM steps: Data Prep -> Modeling -> Artifact Saving.
Usage: python train_and_save_models.py
"""

import os
import glob
import json
import time
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from xgboost import XGBClassifier

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def load_and_clean_data(sample_size=100000):
    print(f"[1/3] Loading and cleaning data (sample: {sample_size} rows)...")
    
    csv_files = glob.glob(os.path.join(DATA_RAW_DIR, "**", "*.csv"), recursive=True)
    csv_files = [f for f in csv_files if "WorkingHours" in f]
    
    if not csv_files:
        raise FileNotFoundError("No CICIDS2017 CSV files found in data/raw/")

    # Load with latin-1 encoding
    df = pd.read_csv(csv_files[0], nrows=sample_size, encoding='latin-1')
    
    # Clean columns (strip spaces, remove duplicates)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.duplicated()]
    
    # Clean labels (remove non-ASCII characters)
    df['Label'] = df['Label'].str.replace(r'[^\x00-\x7F]+', ' ', regex=True).str.strip()
    
    # Handle Inf and NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    # Create binary target (0 = BENIGN, 1 = ATTACK)
    df['Target'] = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)
    
    X = df.drop(columns=['Label', 'Target'])
    y = df['Target']
    
    print(f"   -> Data ready. Shape: {X.shape}")
    return X, y

def train_models(X_train, y_train):
    print("[2/3] Training models...")
    
    # 1. XGBoost
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count
    
    print(f"   -> Training XGBoost (scale_pos_weight={scale_pos_weight:.2f})...")
    xgb_model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric="logloss",
        n_jobs=-1
    )
    xgb_model.fit(X_train, y_train)
    
    # 2. Isolation Forest (Train only on BENIGN traffic)
    print("   -> Training Isolation Forest...")
    X_train_benign = X_train[y_train == 0]
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.02,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train_benign)
    
    return xgb_model, iso_forest

def save_artifacts(xgb_model, iso_forest, features_list):
    print("[3/3] Saving artifacts and metadata...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Save models
    joblib.dump(xgb_model, os.path.join(MODELS_DIR, "xgb_nids.joblib"))
    joblib.dump(iso_forest, os.path.join(MODELS_DIR, "iso_forest_nids.joblib"))
    
    # Save metadata (CRUCIAL for FastAPI)
    metadata = {
        "features": features_list,
        "optimal_threshold_xgb": 0.08, # Found during Notebook 05 evaluation
        "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0.0"
    }
    
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"   -> Models and metadata saved to {MODELS_DIR}")

def main():
    start_time = time.time()
    
    # Run Pipeline
    X, y = load_and_clean_data(sample_size=100000)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    xgb_model, iso_forest = train_models(X_train, y_train)
    
    save_artifacts(xgb_model, iso_forest, X_train.columns.tolist())
    
    elapsed = time.time() - start_time
    print(f"[DONE] Pipeline completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()