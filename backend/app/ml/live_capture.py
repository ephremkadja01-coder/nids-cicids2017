from scapy.all import sniff, IP, TCP
import requests
import time

# ⚠️ Remplace par le nom de ton interface réseau (ex: "eth0", "wlan0", "en0")
INTERFACE = "wlp2s0"
API_URL = "http://127.0.0.1:8000/api/v1/agent"

def process_packet(packet):
    # On ne garde que les paquets TCP avec une adresse IP
    if IP in packet and TCP in packet:
        # Extraction des features (exemple simple)
        features = {
            "Destination Port": packet[TCP].dport,
            "Flow Duration": 0,  # Scapy ne calcule pas la durée par défaut
            "Total Fwd Packets": 1,
            # ... Ajoute ici d'autres features extraites du paquet ...
        }
        
        print(f"📦 Paquet capturé : {packet[IP].src} -> {packet[IP].dst} (Port {packet[TCP].dport})")
        
        # Envoi à ton API pour analyse
        try:
            response = requests.post(API_URL, json={
                "prompt": "Analyse ce paquet réseau en temps réel.",
                "features": features
            })
            result = response.json()
            print(f"🤖 Verdict de l'IA : {result.get('verdict')} (Confiance : {result.get('probability')})")
        except Exception as e:
            print(f"❌ Erreur API : {e}")

print(f"👀 Écoute du trafic sur l'interface {INTERFACE}...")
sniff(iface=INTERFACE, prn=process_packet, store=False)