.PHONY: install backend frontend

install:
	cd backend && python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
	cd frontend && npm ci

backend:
	cd backend && ./run.sh

frontend:
	cd frontend && npm run dev
