#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- Pre-test Setup ---
echo "--- Pre-test Setup ---"

# Create the test database if it doesn't exist
# Redirect stderr to /dev/null to suppress "database already exists" error
createdb test_smart_queue 2>/dev/null || true

# Set PYTHONPATH for the application
export PYTHONPATH=$PYTHONPATH:/home/vast/repos/smart_tasks_queue/app

# Apply database migrations to the test database
echo "Applying database migrations..."
/opt/grv/venv/smart_queue/bin/alembic upgrade head --directory app

echo "Pre-test setup complete."
