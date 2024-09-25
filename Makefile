check:
	@echo "Starting linting"
	ruff check .
	flake8 .


run_app:
	python3 -m app.main

run_bot:
	python3 -m bot.main

run_dev_db_docker:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up postgres redis

run_dev_bot_docker:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up bot

prod-up:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d

prod-down:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod down