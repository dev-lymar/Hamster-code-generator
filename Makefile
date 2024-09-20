check:
	@echo "Starting linting"
	ruff check .
	flake8 .


run_app:
	python3 -m app.main

run_bot:
		python3 -m bot.main