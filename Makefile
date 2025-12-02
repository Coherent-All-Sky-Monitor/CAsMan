.PHONY: docs test coverage update-docs install install-dev clean format venv

# Default target
all: install test

# Virtual environment setup
venv:
	@if [ ! -d .venv ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo "✅ Virtual environment created at .venv"; \
		echo "To activate: source .venv/bin/activate"; \
	else \
		echo "✅ Virtual environment already exists at .venv"; \
	fi

# Installation targets
install: venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "Installing in virtual environment..."; \
		.venv/bin/pip install -e .; \
	else \
		echo "Installing in active virtual environment..."; \
		python3 -m pip install -e .; \
	fi

install-antenna: venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		.venv/bin/pip install -e ".[antenna]"; \
	else \
		python3 -m pip install -e ".[antenna]"; \
	fi

install-dev: venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		.venv/bin/pip install -e ".[dev]"; \
	else \
		python3 -m pip install -e ".[dev]"; \
	fi

# Clean installation (useful for new machines)
install-clean: clean venv
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		.venv/bin/pip uninstall -y casman || true; \
		.venv/bin/pip install -e .; \
	else \
		python3 -m pip uninstall -y casman || true; \
		python3 -m pip install -e .; \
	fi
	@echo "✅ Clean installation complete"

# Testing targets
test:
	python3 -m pytest

test-verbose:
	python3 -m pytest -v

test-coverage:
	python3 -m pytest --cov=casman --cov-report=term-missing

coverage:
	coverage run -m pytest
	coverage report --include="casman/*"
	coverage html --include="casman/*"

# Documentation targets
docs:
	cd docs && python3 generate_docs.py

update-docs: docs
	python3 .github/scripts/update_coverage.py
	@echo "✅ Auto-generated documentation and coverage info updated"

# Development workflow
check: test coverage

# Troubleshooting
troubleshoot:
	@echo "🔍 Running CAsMan installation diagnostics..."
	@echo "Python version:"
	python3 --version
	@echo "Package location:"
	python3 -c "import casman; print(casman.__file__)" 2>/dev/null || echo "❌ casman package not found"
	@echo "CLI import test:"
	python3 -c "from casman.cli import main; print('✅ CLI import successful')" 2>/dev/null || echo "❌ CLI import failed"
	@echo "Entry point test:"
	which casman 2>/dev/null || echo "❌ casman command not found in PATH"
	@echo "🔍 Diagnostics complete"

format:
	black casman/ tests/
	isort casman/ tests/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage .pytest_cache/ 2>/dev/null || true

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
	@echo "  venv            - Create virtual environment (.venv)"
	@echo "  install         - Create venv and install package"
	@echo "  install-antenna - Create venv and install antenna module only"
	@echo "  install-dev     - Create venv and install with dev dependencies"
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
