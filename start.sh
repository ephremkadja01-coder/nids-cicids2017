#!/bin/bash
echo "🚀 Démarrage du NIDS SOC..."

# 1. Backend
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 2. Frontend
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 3

# 3. Scapy
echo "⚠️  Entre ton mot de passe pour le sniffer réseau :"
sudo $PWD/venv/bin/python -m backend.app.ml.live_capture > sniffer.log 2>&1 &
SNIFFER_PID=$!

echo "✅ Tout tourne ! Ouvre http://localhost:5173"
echo "⛔ Pour arrêter : kill $BACKEND_PID $FRONTEND_PID $SNIFFER_PID"