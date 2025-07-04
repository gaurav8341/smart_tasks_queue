#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- Pre-test Setup ---
./pre_test.sh

# --- Run Tests ---
echo "--- Running Tests ---"
/opt/grv/venv/smart_queue/bin/pytest tests/test_job_routes.py

# --- Post-test Cleanup ---
./post_test.sh

echo "Test script finished."