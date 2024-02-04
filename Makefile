.ONESHELL:

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON := python3

help:  ## Help command of Makefile
	@$(PYTHON) <(curl -sSL https://gist.githubusercontent.com/arv-anshul/84a87b6ac9b15f51b9b8d0cdeda33f5f/raw/f48d6fa8d2e5e5769af347e8baa2677cc254c5c6/make_help_decorator.py)

# ---------------------------------- Project Apps ---------------------------------------

.PHONY: st api

st:  ## Run streamlit app
	cd frontend && streamlit run README.py

api:  ## Run FastAPI instance using `python` command
	cd backend && $(PYTHON) app.py

# ------------------------- Code Linting && Formatting ---------------------------------

lint:  ## Run `ruff` linter
	@ruff .

lint-fix:  ## Fix the "fixable" lintin errors
	@ruff . --fix

format:  ## Format with `ruff`
	@ruff format .

# ---------------------------------- Git Hooks ------------------------------------------

PRE_COMMIT_YAML := .pre-commit-config.yaml

install-hooks: $(PRE_COMMIT_YAML)  ## Install `pre-commit-hooks` on local directory [see: https://pre-commit.com]
	$(PYTHON) -m pip install pre-commit
	pre-commit install --install-hooks -c $<

pc-all: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on all files
	pre-commit run --all-files -c $<

pc: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on staged files
	pre-commit run -c $<
