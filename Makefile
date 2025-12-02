.PHONY: docs test coverage update-docs install install-dev clean format

# Default target
all: install test

# Installation targets
install:
	pip install -e .

install-antenna:
	pip install -e ".[antenna]"

install-dev:
	pip install -e ".[dev]"

# Clean installation (useful for new machines)
install-clean: clean
	pip uninstall -y casman || true
	pip install -e .
	@echo "✅ Clean installation complete"

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
	@echo "✅ Auto-generated documentation and coverage info updated"

# Development workflow
check: test coverage

# Troubleshooting
troubleshoot:
	@echo "🔍 Running CAsMan installation diagnostics..."
	@echo "Python version:"
	python --version
	@echo "Package location:"
	python -c "import casman; print(casman.__file__)" 2>/dev/null || echo "❌ casman package not found"
	@echo "CLI import test:"
	python -c "from casman.cli import main; print('✅ CLI import successful')" 2>/dev/null || echo "❌ CLI import failed"
	@echo "Entry point test:"
	which casman 2>/dev/null || echo "❌ casman command not found in PATH"
	@echo "🔍 Diagnostics complete"

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
dev: clean test update-docs
	@echo "✅ Development checks complete"

# Release preparation
release-prep: clean test update-docs
	@echo "✅ Ready for release"

# Service management (Linux systemd only)
install-service:
	@echo "Installing CAsMan as a systemd service..."
	sudo bash scripts/install_service.sh

uninstall-service:
	@echo "Uninstalling CAsMan systemd service..."
	sudo bash scripts/uninstall_service.sh

update-service:
	@echo "Updating CAsMan service..."
	sudo bash scripts/update_service.sh

check-service:
	@echo "Checking CAsMan service health..."
	bash scripts/check_service.sh

service-status:
	sudo systemctl status casman-web.service

service-logs:
	sudo journalctl -u casman-web.service -f

# Help target
help:
	@echo "Available targets:"
	@echo "  install         - Install package in development mode"
	@echo "  install-antenna - Install antenna module only (minimal dependencies)"
	@echo "  install-dev     - Install with development dependencies"
	@echo "  install-clean   - Clean uninstall and reinstall"
	@echo "  test           - Run all tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  coverage       - Run tests with coverage report"
	@echo "  docs           - Generate documentation"
	@echo "  update-docs    - Update docs and coverage info"
	@echo "  format         - Format code with black and isort"
	@echo "  clean          - Remove build artifacts"
	@echo "  setup-hooks    - Install pre-commit hooks"
	@echo "  dev-setup      - Set up development environment"
	@echo "  dev            - Full development check (clean, lint, test, docs)"
	@echo "  troubleshoot   - Run installation diagnostics"
	@echo "  install-service    - Install as systemd service (Linux only)"
	@echo "  uninstall-service  - Remove systemd service"
	@echo "  update-service     - Update running service"
	@echo "  check-service      - Health check for service"
	@echo "  service-status     - Show service status"
	@echo "  service-logs       - Follow service logs"
	@echo "  help           - Show this help message"
