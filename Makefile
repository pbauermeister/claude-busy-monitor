# Just type 'make' to get help.

SHELL := /bin/bash
VENV  ?= .venv

.PHONY: help venv require lint format test build publish clean

help: ## print this help
	@echo "Usage: make [TARGET]..."
	@echo
	@echo "TARGETs:"
	@grep -E '^[a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?##"}; {printf "  %-12s %s\n", $$1, $$2}'

venv: ## create the local virtual environment ($(VENV)/) via uv
	uv venv $(VENV)
	@echo
	@echo "Now please run:"
	@echo "  source $(VENV)/bin/activate"

require: ## install runtime + dev dependencies into the venv
	uv sync --extra dev

lint: ## run ruff lint
	uv run ruff check src

format: ## run ruff format (in-place)
	uv run ruff format src

test: ## run pytest
	uv run pytest

build: ## build wheel + sdist into dist/
	uv build

publish: build ## upload wheel + sdist to PyPI (user-only)
	uv publish

clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
