export PATH := $(HOME)/.local/bin:$(PATH)

.PHONY: help install backend frontend test test-backend test-frontend fetch-kernels inspect-dem clean

help:
	@echo "LunaNav — Full-Stack Lunar Landing Site Navigator (P1 + P2 + P3 + P4 + P5)"
	@echo ""
	@echo "Targets:"
	@echo "  make install        Install Python backend and Node frontend dependencies"
	@echo "  make backend        Start FastAPI backend server on http://localhost:8000"
	@echo "  make frontend       Start Vite React frontend on http://localhost:5173"
	@echo "  make test           Run all backend (P2/P3/P4/P5) and frontend (P1) tests"
	@echo "  make test-backend   Run pytest suite (astro + terrain + decision + API)"
	@echo "  make test-frontend  Run frontend Vitest unit tests"
	@echo "  make fetch-kernels  Download NASA NAIF SPICE kernels into data/raw/kernels/"
	@echo "  make inspect-dem    Inspect LOLA south-pole DEM coverage and metadata"
	@echo "  make clean          Remove cached scenario artifacts and temporary build files"

install:
	python3 -m pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && PYTHONPATH=. python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test: test-backend

test-backend:
	cd backend && python3 -m pytest -v

test-frontend:
	cd frontend && npm test -- --run

fetch-kernels:
	PYTHONPATH=backend python3 scripts/astro/fetch_kernels.py

inspect-dem:
	PYTHONPATH=backend python3 scripts/terrain/inspect_dem.py

clean:
	rm -rf data/cache/scenarios/*.json
	find backend -name "__pycache__" -type d -exec rm -rf {} +

