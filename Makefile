PYTHON := python3

STREAMLIT := README.py
API := api/app.py

.PHONY: st api

note:
	code "/Users/iarv/Documents/OBSIDIAN/Learning Diary/Projects Note/YT History Analyser.md"

st: $(STREAMLIT)
	@streamlit run $<

api: $(API)
	@python3 -m api.app
	# @uvicorn --reload api.app:app

# ---------------------------------- Git Hooks ------------------------------------------

PRE_COMMIT_YAML := .configs/.pre-commit-config.yaml

install-hooks: $(PRE_COMMIT_YAML)  ## Install `pre-commit-hooks` on local directory [see: https://pre-commit.com]
	$(PYTHON) -m pip install pre-commit
	pre-commit install --install-hooks -c $<

pc-all: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on all files
	pre-commit run --all-files -c $<

pc: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on staged files
	pre-commit run -c $<
