FROM python:3.12.2-slim

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /assistant

COPY requirements.txt /assistant/

RUN pip install --upgrade pip \
 && pip install -r requirements.txt

COPY . .

RUN chmod +x /assistant/run_migrations.sh