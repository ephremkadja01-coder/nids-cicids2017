# ---------------------------------------------------------
# NIDS CICIDS2017 - Makefile
# ---------------------------------------------------------

SHELL := /bin/bash

.PHONY: help install start stop test clean train

# Variables
VENV = venv
PYTHON = $(PWD)/$(VENV)/bin/python
UVICORN = ../$(VENV)/bin/uvicorn
PYTEST = ../$(VENV)/bin/pytest

help:
	@echo "Available commands:"
	@echo "  make install   : Setup venv and install Python/Node dependencies"
	@echo "  make start     : Run API, Frontend, and Scapy network sniffer"
	@echo "  make stop      : Stop all processes"
	@echo "  make train     : Retrain the XGBoost model"
	@echo "  make test      : Run unit tests"
	@echo "  make clean     : Remove caches and logs"

install:
	@echo "Installing Python dependencies..."
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "Installing Frontend dependencies..."
	cd frontend && npm install
	@echo "Done. Run 'make start' to launch the application."

start:
	@echo "Starting Backend..."
	cd backend && $(UVICORN) app.main:app --reload > ../backend.log 2>&1 &
	@echo "Starting Frontend..."
	cd frontend && npm run dev > ../frontend.log 2>&1 &
	@sleep 3
	@echo "Scapy sniffer requires sudo privileges."
	@sudo -v
	@echo "Starting Scapy sniffer..."
	@sudo $(PYTHON) -m backend.app.ml.live_capture > sniffer.log 2>&1 &
	@echo "All services running. Open: http://localhost:5173"
	@echo "To stop everything, run: make stop"

stop:
	@echo "Stopping processes..."
	@pkill -f "uvicorn" || true
	@pkill -f "vite" || true
	@sudo pkill -f "live_capture" || true
	@echo "All services stopped."

train:
	@echo "Retraining XGBoost model..."
	cd ml && $(PYTHON) train_and_save_models.py
	@echo "Models updated successfully."

test:
	@echo "Running tests..."
	cd backend && $(PYTEST) tests/ -v || true

clean:
	@echo "Cleaning up..."
	rm -f backend.log frontend.log sniffer.log
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."