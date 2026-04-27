# Just type 'make' to get help.
# First run on a fresh box: 'make require', then 'make help'.
#
# ============================================================================
# CONVENTIONS WHEN EDITING THIS FILE — read before adding/changing targets.
# ============================================================================
#
# 1. Target dependencies — STRICT TWO-LEVEL MODEL:
#    - Low-level  targets: no other-target deps; recipe does ONE thing.
#    - High-level targets: compose low-levels only; NO high→high (neither
#      via `target: deps` lines nor via `$(MAKE) X` submakes in recipes).
#      MARK each high-level target by putting a COLON in its `##` doc
#      string: `<short purpose>: <low-level summary>`. The colon is the
#      formal marker — no naming convention does the same job. The summary
#      after the colon is informative (e.g. `lint unit smoke`); it need
#      not enumerate every composed target. Low-level doc strings MUST
#      NOT contain a colon.
#    High-level targets live with their purpose group; no dedicated section.
#    Audit: scan every `target: …` line and every `$(MAKE) …` in recipes;
#    each referent must be a low-level target.
#
# 2. Help docstrings — ≤60 CHARS (so `make help` lines fit 80 columns).
#    Each target's doc follows `##` on its target line.
#    `make help` prints `  <target><pad-to-col-20><doc>`, room = 60 cols.
#    Verify after edits: `make help | awk '{print length}' | sort -nr | head`.
#
# 3. Order targets within a section by LOGICAL CALL SEQUENCE — the order a
#    user would naturally invoke them (e.g. install before verify-installed;
#    uninstall before verify-uninstalled). High-level targets typically come
#    last (they call the low-levels above), unless a high-level is the
#    recommended entry (e.g. publish-quality before publish in Publish::).
# ============================================================================

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

.PHONY: check
check: lint test-unit test-smoke ## CI/pre-PR check: lint unit smoke

################################################################################
## Tests:: ##

.PHONY: test-unit
test-unit: ## run unit tests (fast, no I/O)
	uv sync --extra dev
	uv run pytest tests/unit

.PHONY: test-smoke
test-smoke: ## run smoke tests (subprocess; no real Claude)
	uv sync --extra dev
	uv run pytest tests/smoke

.PHONY: test-e2e
test-e2e: ## run e2e tests (slow; drives real Claude Code)
	uv sync --extra dev --extra e2e
	uv run pytest tests/e2e

.PHONY: test-full
test-full: test-unit test-smoke ## fast default tests: unit smoke

.PHONY: test
test: test-unit test-smoke ## test-full alias: unit smoke

################################################################################
## Build and install:: ##

.PHONY: build
build: ## build wheel + sdist into dist/
	uv build

.PHONY: install
install: ## install in user account (CLI on ~/.local/bin/) (1)
	uv tool install --reinstall .

.PHONY: verify-installed
verify-installed: ## assert command present and --version matches CHANGES.md
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

.PHONY: uninstall
uninstall: ## uninstall from user account (1)
	uv tool uninstall claude-busy-monitor

.PHONY: verify-uninstalled
verify-uninstalled: ## assert command absent
	@if [ -e "$(CLI)" ]; then \
		echo "verify-uninstalled: $(CLI) still present (run 'make uninstall' first)" >&2; exit 1; \
	fi; \
	echo "verify-uninstalled: OK ($(CLI) absent)"

.PHONY: install-legacy
install-legacy: ## install lib user-wide (1) (2)
	uv pip install --user . || pip install --user --break-system-packages .

.PHONY: uninstall-legacy
uninstall-legacy: ## uninstall lib user-wide (1) (2)
	pip uninstall -y claude-busy-monitor || pip uninstall -y --break-system-packages claude-busy-monitor

.PHONY: cycle
cycle: ## from scratch: uninstall clean lint tests install verify (1)
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

################################################################################
## Publish:: ##

.PHONY: publish-quality
publish-quality: ## pre-publish gate: lint tests build reinstall verify (1)
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

.PHONY: publish
publish: ## upload to PyPI (raw; use publish-quality first)
	uv publish

################################################################################
## Cleanup:: ##

.PHONY: clean
clean: ## remove venv, build artefacts, caches
	rm -rf $(VENV) dist build *.egg-info .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +


################################################################################
##
## Notes:
## - All targets activate .venv for themselves.
## - (1) modifies user account.
## - (2) temporary hack for Python code not using venv.
