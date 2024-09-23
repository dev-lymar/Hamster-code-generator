#!/bin/bash

echo "⏳ Waiting for Postgres to be ready..."
until pg_isready -h $DATABASE_HOST -p 5432 -U $DATABASE_USER; do
  sleep 1
done

echo "✅ Postgres is ready!"

echo "🚀 Running Alembic migrations..."
alembic upgrade head