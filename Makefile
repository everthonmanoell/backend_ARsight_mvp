.PHONY: install run test clean docker-build docker-run

# Install dependencies
install:
	poetry install

# Run API
run:
	poetry run ar-api

# Run in development mode
dev:
	poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest tests/

# Run batch illumination test
test-batch:
	poetry run python tests/test_illumination_batch.py

# Clean cache and logs
clean:
	rm -rf __pycache__ app/__pycache__ app/*/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf logs/*.log
	rm -rf outputs/*

# Docker build for Jetson
docker-build:
	docker build -f docker/Dockerfile.jetson -t ar-diagnostic-mvp:jetson .

# Docker run with GPU
docker-run:
	docker run --rm --gpus all -p 8000:8000 ar-diagnostic-mvp:jetson

# Docker compose up
docker-up:
	docker-compose up -d

# Docker compose down
docker-down:
	docker-compose down

# Format code
format:
	poetry run black app/ tests/

# Lint code
lint:
	poetry run flake8 app/ tests/

# Help
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with Poetry"
	@echo "  make run          - Run API in production mode"
	@echo "  make dev          - Run API in development mode (auto-reload)"
	@echo "  make test         - Run pytest tests"
	@echo "  make test-batch   - Run batch illumination test"
	@echo "  make clean        - Clean cache and logs"
	@echo "  make docker-build - Build Docker image for Jetson"
	@echo "  make docker-run   - Run Docker container with GPU"
	@echo "  make docker-up    - Start Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose"
