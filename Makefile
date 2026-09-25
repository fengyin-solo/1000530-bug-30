.PHONY: install backend frontend

install:
	cd backend && if ! .venv/bin/python --version >/dev/null 2>&1; then rm -rf .venv && python3 -m venv .venv; fi && .venv/bin/pip install -r requirements.txt
	cd frontend && npm ci

backend:
	cd backend && ./run.sh

frontend:
	cd frontend && npm run dev
