.PHONY: install dev lint format test migrate docker clean help

help:
	@echo "EquityIQ Development Commands:"
	@echo "  make install  - Install backend and frontend dependencies"
	@echo "  make dev      - Start development services (backend + frontend)"
	@echo "  make lint     - Run code quality/lint checks (Ruff, import-linter, etc.)"
	@echo "  make format   - Run auto-formatting (Ruff)"
	@echo "  make test     - Run test suites (pytest)"
	@echo "  make migrate  - Run database migrations"
	@echo "  make docker   - Spin up local Docker services (Postgres, Redis)"
	@echo "  make clean    - Remove build artifacts, pycache, caches"

install:
	pip install -e backend/.[dev]
	cd frontend && npm install

dev:
	@echo "Running local dev environment requires concurrent backend and frontend runs."
	@echo "To run backend: uvicorn app.main:app --reload --app-dir backend"
	@echo "To run frontend: cd frontend && npm run dev"

lint:
	ruff check backend/app
	mypy backend/app
	import-linter --config backend/.import-linter.cfg

format:
	ruff format backend/app

test:
	pytest backend/tests

migrate:
	cd backend && alembic upgrade head

docker:
	docker compose -f infra/docker-compose.yml up -d

clean:
	rm -rf backend/build/ backend/dist/ backend/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
