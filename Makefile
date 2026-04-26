# Just type 'make' to get help.
# First run on a fresh box: 'make install-uv', then 'make help'.

SHELL := /bin/bash
VENV  ?= .venv

################################################################################
## General commands:: ##

.PHONY: help
help: ## print this help
	@echo "Usage: make [TARGET]..."
	@echo
	@echo "TARGETs:"

	@# capture section headers and documented targets:
	@grep -E '^#* *[ a-zA-Z_-]+:.*?##.*$$' Makefile \
	| awk 'BEGIN {FS = ":[^:]*?##"}; {printf "  %-19s%s\n", $$1, $$2}' \
	| sed -E 's/^ *#+/\n/g' \
	| sed -E 's/ +$$//g' \
	| sed -E 's/\\n/\n                      /g'

	@# capture notes:
	@grep -E '^##[^#]*$$' Makefile | sed -E 's/^## ?//g'

################################################################################
## Setup:: ##

.PHONY: install-uv
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

.PHONY: _venv
_venv: # create the local venv via uv (idempotent)
	@if [ -x $(VENV)/bin/python ]; then \
		echo "$(VENV) already exists — not recreating."; \
	else \
		uv venv --quiet $(VENV) && echo "Created $(VENV)."; \
	fi

.PHONY: venv-activate
venv-activate: _venv ## sync deps into .venv and start an interactive shell with it activated
	uv sync --extra dev
	@bash --rcfile <(echo "unset MAKELEVEL"; cat ~/.bashrc .venv/bin/activate)

################################################################################
## Quality:: ##

.PHONY: lint
lint: ## run ruff lint
	uv run ruff check src

.PHONY: format
format: ## run ruff format (in-place)
	uv run ruff format src

.PHONY: test
test: ## run pytest
	uv run pytest

################################################################################
## Build and install:: ##

.PHONY: build
build: ## build wheel + sdist into dist/
	uv build

.PHONY: install
install: ## install in the user's account (CLI on ~/.local/bin/)
	uv tool install --force .

.PHONY: uninstall
uninstall: ## uninstall from the user's account
	uv tool uninstall claude-busy-monitor

.PHONY: publish
publish: build ## upload wheel + sdist to PyPI (user-only)
	uv publish

################################################################################
## Cleanup:: ##

.PHONY: clean
clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
