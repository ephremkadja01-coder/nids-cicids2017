import requests
import time

# L'adresse de ton API en temps réel
URL = "http://127.0.0.1:8000/api/v1/predict-live"

print("💥 Lancement de la simulation d'attaque DDoS...")

# On envoie 5 "flux" avec des caractéristiques d'attaque
for i in range(5):
    payload = {
        "features": {
            "Destination Port": 80,          # Port HTTP (souvent ciblé)
            "Flow Duration": 999999,         # Flux anormalement long
            "Total Fwd Packets": 10000,      # Énorme volume de paquets
            "Total Backward Packets": 0,
            "Flow Bytes/s": 99999999,        # Débit massif
            "SYN Flag Count": 5000,          # Indicateur de SYN Flood (DDoS)
            "Fwd Packet Length Mean": 1500.0 # Paquets remplis au max
        }
    }
    
    try:
        response = requests.post(URL, json=payload)
        if response.status_code == 200:
            print(f"✅ Attaque envoyée ({i+1}/5)")
        else:
            print(f"⚠️ Erreur API : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur : {e}")
        
    # Petite pause pour voir les alertes s'afficher une par une
    time.sleep(1)

print("🏁 Simulation terminée.")