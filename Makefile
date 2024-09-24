check:
	@echo "Starting linting"
	ruff check .
	flake8 .


run_app:
	python3 -m app.main

run_bot:
	python3 -m bot.main

run_dev_db_docker:
	docker-compose -f docker-compose.dev.yml up postgres redis

run_dev_bot_docker:
	docker-compose -f docker-compose.dev.yml up bot