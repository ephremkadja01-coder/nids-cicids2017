from scapy.all import sniff, IP, TCP
import requests

INTERFACE = "wlp2s0" # Ton interface Wi-Fi
API_URL = "http://127.0.0.1:8000/api/v1/predict-live"

def process_packet(packet):
    if IP in packet and TCP in packet:
        # On simule un flux basé sur le paquet
        features = {
            "Destination Port": float(packet[TCP].dport),
            "Flow Duration": 0.0,
            "Total Fwd Packets": 1.0,
            "Total Backward Packets": 0.0,
            "Total Length of Fwd Packets": float(len(packet)),
            "Total Length of Bwd Packets": 0.0,
            "Fwd Packet Length Max": float(len(packet)),
            "Fwd Packet Length Min": float(len(packet)),
            "Fwd Packet Length Mean": float(len(packet)),
            "Fwd Packet Length Std": 0.0,
        }
        
        try:
            # Envoi ultra-rapide (sans attendre la réponse pour ne pas ralentir la capture)
            requests.post(API_URL, json={"features": features}, timeout=0.5)
        except Exception:
            pass # On ignore les erreurs de timeout pour ne pas crasher le sniffer

print(f"👀 Écoute du trafic sur {INTERFACE} et envoi à l'API...")
sniff(iface=INTERFACE, prn=process_packet, store=False)