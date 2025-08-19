# aiclip - AI-powered ffmpeg CLI
# Development and deployment automation

PYTHON?=python3
VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python
PYTEST=$(VENV)/bin/pytest
AICLIP=$(VENV)/bin/aiclip
RUFF=$(VENV)/bin/ruff
MYPY=$(VENV)/bin/mypy
SAFETY=$(VENV)/bin/safety
BANDIT=$(VENV)/bin/bandit
TWINE=$(VENV)/bin/twine
BUILD=$(VENV)/bin/python -m build

# Colors for output
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

.PHONY: help setup install test lint format clean run demo build publish release docker docs

# Default target
help:
	@echo "$(GREEN)aiclip - Development Commands$(NC)"
	@echo
	@echo "$(YELLOW)Setup & Installation:$(NC)"
	@echo "  setup     - Create virtual environment and install dependencies"
	@echo "  install   - Install package in development mode"
	@echo "  clean     - Remove build artifacts and cache files"
	@echo
	@echo "$(YELLOW)Development:$(NC)"
	@echo "  test      - Run test suite with pytest"
	@echo "  lint      - Check code quality with ruff"
	@echo "  format    - Format code with ruff"
	@echo "  run       - Run aiclip with arguments (use ARGS=)"
	@echo "  demo      - Run demonstration commands"
	@echo
	@echo "$(YELLOW)Release & Publishing:$(NC)"
	@echo "  build     - Build distribution packages"
	@echo "  publish   - Upload to PyPI (production)"
	@echo "  test-pub  - Upload to TestPyPI (testing)"
	@echo "  release   - Full release workflow (test + tag + publish)"
	@echo
	@echo "$(YELLOW)Other:$(NC)"
	@echo "  docs      - Generate and serve documentation"
	@echo "  docker    - Build Docker image"
	@echo "  security  - Run security checks"
	@echo
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make run ARGS='\"convert video.mp4 to 720p\"'"
	@echo "  make test"
	@echo "  make release VERSION=0.2.0"

# Setup and Installation
setup:
	@echo "$(GREEN)Setting up development environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -e .[dev]
	@echo "$(GREEN)Setup complete! Run 'source $(VENV)/bin/activate' to activate.$(NC)"

install: setup

# Testing and Quality
test:
	@echo "$(GREEN)Running test suite...$(NC)"
	$(PYTEST) -v --tb=short

test-cov:
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(PYTEST) -v --cov=ai_ffmpeg_cli --cov-report=html --cov-report=term

lint:
	@echo "$(GREEN)Checking code quality...$(NC)"
	@test -f $(RUFF) || $(PIP) install ruff
	$(RUFF) check src tests
	@echo "$(GREEN)Code quality check complete!$(NC)"

format:
	@echo "$(GREEN)Formatting code...$(NC)"
	@test -f $(RUFF) || $(PIP) install ruff
	$(RUFF) format src tests
	$(RUFF) check --fix src tests
	@echo "$(GREEN)Code formatting complete!$(NC)"

security:
	@echo "$(GREEN)Running security checks...$(NC)"
	@test -f $(SAFETY) || $(PIP) install safety
	@test -f $(BANDIT) || $(PIP) install bandit
	$(SAFETY) check
	$(BANDIT) -r src/
	@echo "$(GREEN)Security checks complete!$(NC)"

# Development & Demo
run:
	@echo "$(GREEN)Running aiclip...$(NC)"
	$(AICLIP) $(ARGS)

demo:
	@echo "$(GREEN)Running aiclip demonstrations...$(NC)"
	@echo "$(YELLOW)Demo 1: Convert formats$(NC)"
	$(AICLIP) --dry-run --verbose "convert sample.mov to mp4 h264+aac" || true
	@echo
	@echo "$(YELLOW)Demo 2: Extract audio$(NC)"
	$(AICLIP) --dry-run --verbose "extract audio from demo.mp4 to mp3" || true
	@echo
	@echo "$(YELLOW)Demo 3: Trim video$(NC)"  
	$(AICLIP) --dry-run --verbose "trim first 30 seconds from input.mp4" || true
	@echo
	@echo "$(YELLOW)Demo 4: Create thumbnail$(NC)"
	$(AICLIP) --dry-run --verbose "thumbnail at 10 seconds from input.mp4" || true
	@echo
	@echo "$(YELLOW)Demo 5: Compress video$(NC)"
	$(AICLIP) --dry-run --verbose "compress large-video.mp4 smaller" || true
	@echo
	@echo "$(GREEN)Demo complete! Remove --dry-run to execute commands.$(NC)"

interactive:
	@echo "$(GREEN)Starting interactive mode...$(NC)"
	$(AICLIP)

# Build and Publishing
clean:
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	rm -rf dist/ build/ *.egg-info/
	rm -rf .pytest_cache/ .ruff_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

build: clean
	@echo "$(GREEN)Building distribution packages...$(NC)"
	$(PIP) install --upgrade build
	$(BUILD)
	@echo "$(GREEN)Build complete! Check dist/ directory.$(NC)"

test-pub: build
	@echo "$(GREEN)Publishing to TestPyPI...$(NC)"
	$(PIP) install --upgrade twine
	$(TWINE) upload --repository testpypi dist/*
	@echo "$(GREEN)Published to TestPyPI!$(NC)"
	@echo "Test with: pip install -i https://test.pypi.org/simple/ ai-ffmpeg-cli"

publish: build
	@echo "$(YELLOW)Publishing to PyPI (PRODUCTION)...$(NC)"
	@echo "$(RED)This will publish to the real PyPI! Press Enter to continue or Ctrl+C to cancel.$(NC)"
	@read
	$(PIP) install --upgrade twine
	$(TWINE) upload dist/*
	@echo "$(GREEN)Published to PyPI! 🎉$(NC)"

# Version management
version-check:
	@echo "Current version: $$(grep '^version' pyproject.toml | cut -d'"' -f2)"

version-bump:
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Please specify VERSION. Example: make version-bump VERSION=0.2.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Bumping version to $(VERSION)...$(NC)"
	sed -i.bak 's/^version = .*/version = "$(VERSION)"/' pyproject.toml
	rm -f pyproject.toml.bak
	@echo "$(GREEN)Version updated to $(VERSION)$(NC)"

# Complete release workflow
release: version-check
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)Please specify VERSION. Example: make release VERSION=0.2.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Starting release workflow for version $(VERSION)...$(NC)"
	
	# Run tests first
	@echo "$(YELLOW)Step 1: Running tests...$(NC)"
	make test
	
	# Update version
	@echo "$(YELLOW)Step 2: Updating version...$(NC)"  
	make version-bump VERSION=$(VERSION)
	
	# Build and test publish
	@echo "$(YELLOW)Step 3: Building and testing...$(NC)"
	make test-pub
	
	# Git operations
	@echo "$(YELLOW)Step 4: Creating git tag...$(NC)"
	git add pyproject.toml
	git commit -m "Bump version to $(VERSION)" || true
	git tag -a v$(VERSION) -m "Release version $(VERSION)"
	
	# Final publish
	@echo "$(YELLOW)Step 5: Publishing to PyPI...$(NC)"
	make publish
	
	# Push to git
	@echo "$(YELLOW)Step 6: Pushing to git...$(NC)"
	git push origin main
	git push origin v$(VERSION)
	
	@echo "$(GREEN)Release $(VERSION) complete! 🚀$(NC)"

# Documentation
docs:
	@echo "$(GREEN)Generating documentation...$(NC)"
	$(PIP) install mkdocs mkdocs-material
	mkdocs serve
	@echo "$(GREEN)Documentation served at http://127.0.0.1:8000$(NC)"

# Docker
docker:
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t aiclip:latest .
	@echo "$(GREEN)Docker image built! Run with: docker run -it aiclip:latest$(NC)"

# CI/CD helpers
ci-test: setup test lint security
	@echo "$(GREEN)CI pipeline complete!$(NC)"

pre-commit: format lint test
	@echo "$(GREEN)Pre-commit checks complete!$(NC)"

# Installation verification
verify-install:
	@echo "$(GREEN)Verifying installation...$(NC)"
	$(AICLIP) --version
	$(AICLIP) --help | head -10
	@echo "$(GREEN)Installation verified!$(NC)"

# Development utilities  
deps-update:
	@echo "$(GREEN)Updating dependencies...$(NC)"
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -U -e .[dev]

deps-list:
	@echo "$(GREEN)Installed dependencies:$(NC)"
	$(PIP) list

# Quick commands
check: lint test
	@echo "$(GREEN)All checks passed!$(NC)"

dev: setup demo
	@echo "$(GREEN)Development environment ready!$(NC)"

all: clean setup test lint build
	@echo "$(GREEN)Full pipeline complete!$(NC)"