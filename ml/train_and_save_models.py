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

# Nombre de lignes à lire PAR FICHIER (pour éviter de saturer la RAM)
# 50 000 lignes * 8 fichiers = 400 000 lignes, ce qui est parfait pour l'entraînement.
SAMPLE_SIZE_PER_FILE = 50000 

def load_and_clean_data():
    print(f"[1/3] Chargement de TOUS les fichiers d'attaques ({SAMPLE_SIZE_PER_FILE} lignes/fichier)...")
    
    # On cherche tous les fichiers CSV dans le dossier MachineLearningCVE
    csv_pattern = os.path.join(DATA_RAW_DIR, "**", "MachineLearningCVE", "*.csv")
    csv_files = glob.glob(csv_pattern, recursive=True)
    
    # Fallback si le dossier n'est pas exactement nommé ainsi
    if not csv_files:
        csv_files = glob.glob(os.path.join(DATA_RAW_DIR, "**", "*.csv"), recursive=True)
        csv_files = [f for f in csv_files if "WorkingHours" in f or "DDos" in f or "PortScan" in f]

    if not csv_files:
        raise FileNotFoundError("Aucun fichier CSV CICIDS2017 trouvé.")

    frames = []
    for file_path in sorted(csv_files):
        filename = os.path.basename(file_path)
        print(f"   -> Chargement de {filename}...")
        
        try:
            # On lit seulement un échantillon de chaque fichier
            df_temp = pd.read_csv(file_path, nrows=SAMPLE_SIZE_PER_FILE, encoding='latin-1')
            
            # Nettoyage des noms de colonnes (enlever les espaces)
            df_temp.columns = df_temp.columns.str.strip()
            # Suppression des colonnes dupliquées (le fameux bug de 'Fwd Header Length')
            df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()]
            
            if 'Label' in df_temp.columns:
                # Nettoyage des caractères bizarres dans les labels
                df_temp['Label'] = df_temp['Label'].str.replace(r'[^\x00-\x7F]+', ' ', regex=True).str.strip()
                frames.append(df_temp)
            else:
                print(f"      ⚠️ Pas de colonne 'Label' dans {filename}, ignoré.")
                
        except Exception as e:
            print(f"      ❌ Erreur avec {filename}: {e}")

    # Fusion de tous les échantillons
    print("\n   -> Fusion des données...")
    df = pd.concat(frames, ignore_index=True)
    
    # Nettoyage final (Inf et NaN)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    # Création de la cible binaire (0 = BENIGN, 1 = ATTACK)
    df['Target'] = df['Label'].apply(lambda x: 0 if x == 'BENIGN' else 1)
    
    X = df.drop(columns=['Label', 'Target'])
    y = df['Target']
    
    print(f"\n   -> Dataset final : {X.shape[0]} lignes, {X.shape[1]} colonnes.")
    print(f"   -> Distribution des classes (0=Benign, 1=Attack) :")
    print(y.value_counts(normalize=True) * 100)
    
    return X, y

def train_models(X_train, y_train):
    print("\n[2/3] Entraînement des modèles...")
    
    # 1. XGBoost (Supervisé)
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    # On évite la division par zéro si jamais il n'y a pas d'attaques
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1.0
    
    print(f"   -> Entraînement XGBoost (scale_pos_weight={scale_pos_weight:.2f})...")
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
    
    # 2. Isolation Forest (Non-supervisé, entraîné uniquement sur BENIGN)
    print("   -> Entraînement Isolation Forest (uniquement sur le trafic bénin)...")
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
    print("\n[3/3] Sauvegarde des artefacts...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    joblib.dump(xgb_model, os.path.join(MODELS_DIR, "xgb_nids.joblib"))
    joblib.dump(iso_forest, os.path.join(MODELS_DIR, "iso_forest_nids.joblib"))
    
    metadata = {
        "features": features_list,
        "optimal_threshold_xgb": 0.08, # On garde le seuil qu'on avait trouvé
        "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "2.0.0-all-attacks"
    }
    
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"   -> Modèles et metadata sauvegardés dans {MODELS_DIR}")

def main():
    start_time = time.time()
    
    X, y = load_and_clean_data()
    
    # Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    xgb_model, iso_forest = train_models(X_train, y_train)
    
    save_artifacts(xgb_model, iso_forest, X_train.columns.tolist())
    
    elapsed = time.time() - start_time
    print(f"\n[DONE] Entraînement terminé en {elapsed:.2f} secondes.")

if __name__ == "__main__":
    main()