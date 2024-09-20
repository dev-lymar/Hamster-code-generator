check:
	@echo "Starting linting"
	ruff check .
	flake8 .


run:
	python3 -m app.main