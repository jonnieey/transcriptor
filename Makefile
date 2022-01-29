.DEFAULT_GOAL := help

PY_SRC := src/ tests/

.PHONY: help
help:  ## Print this help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: all
all: lint tests checks

.PHONY: lint
lint: lint-black lint-isort  ## Run linting tools on the code.

.PHONY: lint-black
lint-black:  ## Lint the code using black.
	pdm run black $(PY_SRC)

.PHONY: lint-isort
lint-isort:  ## Sort the imports using isort.
	pdm run isort $(PY_SRC)

.PHONY: tests
tests: run-tests clean-tests

.PHONY: run-tests
run-tests:  ## Run tests using pytest
	@echo -e "RUNNING TESTS\n"
	pdm run pytest tests

.PHONY: clean
clean: clean-tests clean-tmp

.PHONY: clean-tests
clean-tests:  ## Delete temporary tests files.
	@echo -e "REMOVING TEMP TEST DATA\n"
	@rm -rf tests/data/* 2>/dev/null

.PHONY: clean-tmp
clean-tmp:  ## Delete temporary files.
	@echo -e "REMOVING DATA DIRECTORY\n"
	@rm -rf .mypy_cache
	@rm -rf .pytest_cache
	@rm -rf build
	@rm -rf dist
	@find . -type d -name __pycache__ | xargs rm -rf

.PHONY: checks
checks: check-types

.PHONY: check-types
check-types: ## Check types
	pdm run mypy $(PY_SRC)

