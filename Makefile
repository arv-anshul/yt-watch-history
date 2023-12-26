PYTHON := python3

STREAMLIT_APP := README.py
API_APP := app.py

note:
	code "/Users/iarv/Documents/OBSIDIAN/Learning Diary/Projects Note/YT History Analyser.md"

# ---------------------------------- Project Apps ------------------------------------------

.PHONY: st api

st: $(STREAMLIT_APP)
	streamlit run $<

api: $(API_APP)
	$(PYTHON) $<

# ---------------------------------- Git Hooks ------------------------------------------

PRE_COMMIT_YAML := .configs/.pre-commit-config.yaml

install-hooks: $(PRE_COMMIT_YAML)  ## Install `pre-commit-hooks` on local directory [see: https://pre-commit.com]
	$(PYTHON) -m pip install pre-commit
	pre-commit install --install-hooks -c $<

pc-all: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on all files
	pre-commit run --all-files -c $<

pc: $(PRE_COMMIT_YAML)  ## Run `pre-commit` on staged files
	pre-commit run -c $<
