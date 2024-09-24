FROM python:3.12.2-slim

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /assistant

COPY requirements.txt /assistant/

RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY app /assistant/app
COPY bot /assistant/bot
COPY alembic /assistant/alembic
COPY alembic.ini /assistant/alembic.ini
COPY db /assistant/db
COPY config /assistant/config
COPY run_migrations.sh /assistant/run_migrations.sh

RUN chmod +x /assistant/run_migrations.sh