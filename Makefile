.PHONY: install lint test check run preview

install:
	python -m pip install -r requirements-dev.txt

lint:
	python -m ruff check .

test:
	python -m pytest -q

check: lint test
	python scripts/validate_data.py

run:
	streamlit run app.py

preview:
	python scripts/build_preview.py
