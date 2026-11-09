from scapy.all import sniff, IP, TCP
import requests
import threading
import time

INTERFACE = "wlp2s0" # Ton interface Wi-Fi
API_URL = "http://127.0.0.1:8000/api/v1/predict-live"

# Dictionnaire pour stocker les flux en cours d'agrégation
active_flows = {}
# Verrou (Lock) pour éviter les conflits entre le sniffer et le thread qui envoie les données
flows_lock = threading.Lock()

def process_packet(packet):
    if IP in packet and TCP in packet:
        src = packet[IP].src
        dst = packet[IP].dst
        dport = packet[TCP].dport
        
        # La clé unique du flux (Session)
        flow_key = f"{src}->{dst}:{dport}"
        
        with flows_lock:
            if flow_key not in active_flows:
                active_flows[flow_key] = {
                    "start_time": time.time(),
                    "packets": 0,
                    "bytes": 0
                }
            
            # On met à jour les compteurs du flux
            active_flows[flow_key]["packets"] += 1
            active_flows[flow_key]["bytes"] += len(packet)

def flush_flows():
    """Envoie les flux agrégés à l'API toutes les 3 secondes"""
    while True:
        time.sleep(3) # Fenêtre d'agrégation de 3 secondes
        
        with flows_lock:
            if not active_flows:
                continue
            # On copie les flux actuels et on vide le dictionnaire pour la prochaine fenêtre
            flows_to_send = active_flows.copy()
            active_flows.clear()
        
        for flow_key, data in flows_to_send.items():
            # On calcule les vraies features temporelles
            duration = time.time() - data["start_time"]
            packets = data["packets"]
            total_bytes = data["bytes"]
            
            # On construit les features attendues par XGBoost
            features = {
                "Destination Port": float(flow_key.split(":")[-1]),
                "Flow Duration": float(duration),
                "Total Fwd Packets": float(packets),
                "Total Backward Packets": 0.0,
                "Total Length of Fwd Packets": float(total_bytes),
                "Total Length of Bwd Packets": 0.0,
                "Fwd Packet Length Max": float(total_bytes / packets) if packets > 0 else 0.0,
                "Fwd Packet Length Min": float(total_bytes / packets) if packets > 0 else 0.0,
                "Fwd Packet Length Mean": float(total_bytes / packets) if packets > 0 else 0.0,
                "Fwd Packet Length Std": 0.0,
            }
            
            try:
                # On envoie le flux agrégé à l'API
                requests.post(API_URL, json={"features": features}, timeout=1.0)
                print(f"📦 Flux analysé : {flow_key} | {packets} paquets | {duration:.2f}s")
            except Exception as e:
                print(f"❌ Erreur d'envoi à l'API : {e}")

def start_sniffer():
    """Fonction d'écoute (tourne en boucle)"""
    print(f"👀 [SCAPY] Écoute du trafic sur {INTERFACE} avec agrégation de flux...")
    
    # On lance le thread qui envoie les flux toutes les 3 secondes
    flush_thread = threading.Thread(target=flush_flows, daemon=True)
    flush_thread.start()
    
    # On lance l'écoute Scapy
    sniff(iface=INTERFACE, prn=process_packet, store=False)

def run_sniffer_in_background():
    """Lance le sniffer dans un thread séparé pour ne pas bloquer FastAPI"""
    thread = threading.Thread(target=start_sniffer, daemon=True)
    thread.start()