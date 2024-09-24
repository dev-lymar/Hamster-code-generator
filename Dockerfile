FROM python:3.12.2-slim

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /assistant

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY app app
COPY bot bot
COPY alembic alembic
COPY alembic.ini alembic.ini
COPY db db
COPY config config

RUN chmod +x /assistant/run_migrations.sh