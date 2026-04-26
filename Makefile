# Just type 'make' to get help.
# First run on a fresh box: 'make install-uv', then 'make help'.

SHELL := /bin/bash
VENV  ?= .venv

.PHONY: help install-uv venv venv-activate require lint format test build install publish clean

################################################################################                                                           
## General commands:: ##                                                                                                                   

help: ## print this help
	@echo "Usage: make [TARGET]..."
	@echo
	@echo "TARGETs:"
	@grep -E '^[a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?##"}; {printf "  %-14s %s\n", $$1, $$2}'

################################################################################                                                           
## Setup:: ##                                                                                                                              

install-uv: ## install uv (idempotent; Linux/macOS via Astral installer)
	@if command -v uv >/dev/null 2>&1; then \
		echo "uv already installed: $$(uv --version)"; \
	else \
		case "$$(uname -s)" in \
			Linux|Darwin) \
				curl -LsSf https://astral.sh/uv/install.sh | sh ;; \
			MINGW*|MSYS*|CYGWIN*) \
				echo "Windows detected. Run: winget install astral-sh.uv"; exit 1 ;; \
			*) \
				echo "Unsupported OS: $$(uname -s). See https://docs.astral.sh/uv/getting-started/installation/"; exit 1 ;; \
		esac; \
	fi

venv: ## create the local virtual environment ($(VENV)) via uv (idempotent)
	@if [ -x $(VENV)/bin/python ]; then \
		echo "$(VENV) already exists — not recreating."; \
	else \
		uv venv --quiet $(VENV) && echo "Created $(VENV)."; \
	fi

venv-activate: venv ## Activate .venv and start an interactive shell
	@bash --rcfile <(echo "unset MAKELEVEL"; cat ~/.bashrc .venv/bin/activate)

require: venv ## install runtime + dev dependencies into the venv
	uv sync --extra dev

lint: ## run ruff lint
	uv run ruff check src

format: ## run ruff format (in-place)
	uv run ruff format src

test: ## run pytest
	uv run pytest

build: ## build wheel + sdist into dist/
	uv build

install: ## install CLI globally (puts claude-busy-monitor on ~/.local/bin/)
	uv tool install --force .

publish: build ## upload wheel + sdist to PyPI (user-only)
	uv publish

clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
