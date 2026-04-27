# Just type 'make' to get help.
# First run on a fresh box: 'make require', then 'make help'.
#
# Target layering (#11): two levels.
#   Low-level   — no other-target deps, recipe does one thing.
#   High-level  — composes low-levels only (no high→high).
# High-level targets are grouped at the bottom of this file.

SHELL := /bin/bash
VENV  ?= .venv
CLI   ?= $(HOME)/.local/bin/claude-busy-monitor

################################################################################
## General commands:: ##

.PHONY: help
help: ## print this help
	@echo "Usage: make [TARGET]..."
	@echo
	@echo "TARGETs:"

	@# capture section headers and documented targets:
	@grep -E '^#* *[ a-zA-Z0-9_-]+:.*?##.*$$' Makefile \
	| awk 'BEGIN {FS = ":[^:]*?##"}; {printf "  %-18s%s\n", $$1, $$2}' \
	| sed -E 's/^ *#+/\n/g' \
	| sed -E 's/ +$$//g' \
	| sed -E 's/\\n/\n                      /g'

	@# capture notes:
	@grep -E '^##[^#]*$$' Makefile | sed -E 's/^## ?//g'

################################################################################
## Setup:: ##

.PHONY: require
require: ## install uv (idempotent; Linux/macOS via Astral installer)
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

.PHONY: venv-activate
venv-activate: ## start an interactive shell in updated .venv
	uv sync --extra dev
	@bash --rcfile <(echo "unset MAKELEVEL"; cat ~/.bashrc .venv/bin/activate)

################################################################################
## Quality:: ##

.PHONY: lint
lint: ## ruff check + format-check (read-only)
	uv sync --extra dev
	uv run ruff check src
	uv run ruff format --check src

.PHONY: format
format: ## ruff format + lint autofix (modifies code)
	uv sync --extra dev
	uv run ruff format src
	uv run ruff check --fix src

################################################################################
## Tests:: ##

.PHONY: test-unit
test-unit: ## run unit tests (fast, no I/O)
	uv sync --extra dev
	uv run pytest tests/unit

.PHONY: test-smoke
test-smoke: ## run smoke tests (subprocess invocations, no real Claude)
	uv sync --extra dev
	uv run pytest tests/smoke

.PHONY: test-e2e
test-e2e: ## run e2e tests (slow — drives real Claude Code)
	uv sync --extra dev --extra e2e
	uv run pytest tests/e2e

################################################################################
## Build and install:: ##

.PHONY: build
build: ## build wheel + sdist into dist/
	uv build

.PHONY: install
install: ## install in the user's account (CLI on ~/.local/bin/)
	uv tool install --reinstall .

.PHONY: uninstall
uninstall: ## uninstall from the user's account
	uv tool uninstall claude-busy-monitor

.PHONY: verify-installed
verify-installed: ## assert $(CLI) present and --version matches CHANGES.md
	@if [ ! -x "$(CLI)" ]; then \
		echo "verify-installed: missing $(CLI) (run 'make install' first)" >&2; exit 1; \
	fi; \
	EXPECTED=$$(awk -F'[ :]' '/^## Version / {print $$3; exit}' CHANGES.md); \
	if [ -z "$$EXPECTED" ]; then \
		echo "verify-installed: cannot extract version from CHANGES.md" >&2; exit 1; \
	fi; \
	ACTUAL=$$("$(CLI)" --version 2>&1 | awk '{print $$NF}'); \
	if [ "$$ACTUAL" != "$$EXPECTED" ]; then \
		echo "verify-installed: version mismatch (expected $$EXPECTED, got '$$ACTUAL')" >&2; exit 1; \
	fi; \
	echo "verify-installed: OK ($(CLI) v$$ACTUAL)"

.PHONY: verify-uninstalled
verify-uninstalled: ## assert $(CLI) absent
	@if [ -e "$(CLI)" ]; then \
		echo "verify-uninstalled: $(CLI) still present (run 'make uninstall' first)" >&2; exit 1; \
	fi; \
	echo "verify-uninstalled: OK ($(CLI) absent)"

.PHONY: install-legacy
install-legacy: ## install lib user-wide (2)
	uv pip install --user . || pip install --user --break-system-packages .

.PHONY: uninstall-legacy
uninstall-legacy: ## uninstall lib user-wide (2)
	pip uninstall -y claude-busy-monitor || pip uninstall -y --break-system-packages claude-busy-monitor

.PHONY: publish
publish: ## upload wheel + sdist to PyPI (user-only; raw — use publish-quality first)
	uv publish

################################################################################
## Cleanup:: ##

.PHONY: clean
clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

################################################################################
## High-level compositions:: ##

.PHONY: test-full
test-full: test-unit test-smoke ## unit + smoke (fast default)

.PHONY: test
test: test-unit test-smoke ## alias for test-full (same dep set; not nested)

.PHONY: check
check: lint test-unit test-smoke ## lint + unit + smoke (CI / pre-PR convenience)

.PHONY: cycle
cycle: ## full cycle: uninstall → verify → clean → lint+tests → install → verify (1)
	@echo "About to uninstall claude-busy-monitor and rebuild from scratch."
	@echo "Ctrl-C within 2 seconds to abort."
	@sleep 2
	-$(MAKE) uninstall
	$(MAKE) verify-uninstalled
	$(MAKE) clean
	$(MAKE) lint
	$(MAKE) test-unit
	$(MAKE) test-smoke
	$(MAKE) install
	$(MAKE) verify-installed

.PHONY: publish-quality
publish-quality: ## max-quality gate before 'make publish' — verifies, does NOT upload (1)
	@echo "About to run lint + tests + uninstall/install cycle. Does NOT upload."
	@echo "Ctrl-C within 2 seconds to abort."
	@sleep 2
	$(MAKE) lint
	$(MAKE) test-unit
	$(MAKE) test-smoke
	$(MAKE) build
	-$(MAKE) uninstall
	$(MAKE) verify-uninstalled
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) verify-installed
	@echo "publish-quality: all gates green. Run 'make publish' to upload."


################################################################################
##
## Notes:
## - All targets activate .venv for themselves.
## - (1) modifies user account.
## - (2) temporary hack for Python code not using venv.
