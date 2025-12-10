#!/bin/bash

# Script to create a new database migration

echo "Creating database migration..."

cd "$(dirname "$0")/../backend" || exit

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Get migration message from command line or use default
MESSAGE=${1:-"Auto migration"}

# Create migration
alembic revision --autogenerate -m "$MESSAGE"

echo ""
echo "Migration created! Review the file in backend/app/migrations/versions/"
echo "Then run: cd backend && alembic upgrade head"

