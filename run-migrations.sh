#!/bin/bash

echo "Running database migrations..."

echo "Waiting for PostgreSQL to be ready..."
sleep 10

echo "Running Auth Service migrations..."
docker-compose exec auth-service alembic upgrade head

echo "Running Movie Service migrations..."
docker-compose exec movie-service alembic upgrade head

echo "Migrations completed!"