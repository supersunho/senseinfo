# backend/start.sh
#!/bin/bash

# InfoSense Backend Start Script

set -e

echo "Starting InfoSense Backend..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U infosense; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! redis-cli -h redis ping; do
  sleep 1
done
echo "Redis is ready!"

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
