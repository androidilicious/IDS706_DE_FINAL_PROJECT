# Makefile for Olist E-Commerce Data Pipeline

.PHONY: help install test lint format clean run docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install       - Install Python dependencies"
	@echo "  make test          - Run all tests with coverage"
	@echo "  make lint          - Run code linting"
	@echo "  make format        - Format code with black"
	@echo "  make run           - Run complete pipeline"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run pipeline in Docker"
	@echo "  make clean         - Remove generated files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v --cov=ingestion --cov=transformation --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 ingestion/ transformation/ tests/ --count --statistics
	@echo "Linting complete!"

format:
	black ingestion/ transformation/ tests/
	@echo "Code formatted!"

run:
	cd ingestion && python ingestion_pipeline.py

run-transform:
	python transformation/analyze_with_polars.py

run-tests:
	python tests/test_data_quality.py

test-connections:
	python ingestion/test_connections.py

docker-build:
	docker build -t olist-pipeline:latest .

docker-run:
	docker-compose up --build pipeline

docker-test:
	docker-compose up test

docker-clean:
	docker-compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -f {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	@echo "Cleaned up generated files!"

setup:
	@echo "Setting up Olist Data Pipeline..."
	@echo "Step 1: Install dependencies"
	make install
	@echo "Step 2: Test connections"
	make test-connections
	@echo "Step 3: Ready to run!"
	@echo "Run 'make run' to start the pipeline"
