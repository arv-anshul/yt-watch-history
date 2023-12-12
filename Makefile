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
