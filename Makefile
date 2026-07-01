.PHONY: install install-backend install-frontend dev-backend dev-frontend test lint build

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

build:
	cd frontend && npm run build
