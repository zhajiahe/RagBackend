.PHONY: format lint

format:
	ruff format .

format-check:
	ruff format --check .

lint:
	ruff check .

lint-fix:
	ruff check --fix .
