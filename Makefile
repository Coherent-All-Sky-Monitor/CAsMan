.PHONY: docs test coverage update-docs install install-dev clean lint format

# Default target
all: install test

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing targets
test:
	python -m pytest

test-verbose:
	python -m pytest -v

test-coverage:
	python -m pytest --cov=casman --cov-report=term-missing

coverage:
	coverage run -m pytest
	coverage report --include="casman/*"
	coverage html --include="casman/*"

# Documentation targets
docs:
	cd docs && python generate_docs.py

update-docs: docs
	python .github/scripts/update_coverage.py
	@echo "✅ Documentation and coverage info updated"

# Development workflow
check: lint test coverage

# Linting and formatting
lint:
	flake8 casman/ tests/
	pylint casman/ tests/ || true

format:
	black casman/ tests/
	isort casman/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

# Git hooks setup
setup-hooks:
	cp .github/hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook installed"

# Development setup
dev-setup: install-dev setup-hooks
	@echo "✅ Development environment set up"

# Quick development workflow
dev: clean lint test update-docs
	@echo "✅ Development checks complete"

# Release preparation
release-prep: clean test update-docs
	@echo "✅ Ready for release"

# Help target
help:
	@echo "Available targets:"
	@echo "  install      - Install package in development mode"
	@echo "  install-dev  - Install with development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  docs         - Generate documentation"
	@echo "  update-docs  - Update docs and coverage info"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  clean        - Remove build artifacts"
	@echo "  setup-hooks  - Install pre-commit hooks"
	@echo "  dev-setup    - Set up development environment"
	@echo "  dev          - Full development check (clean, lint, test, docs)"
	@echo "  help         - Show this help message"
