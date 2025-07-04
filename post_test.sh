#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- Post-test Cleanup ---
echo "--- Post-test Cleanup ---"

# Drop the test database
# Redirect stderr to /dev/null to suppress "database does not exist" error
dropdb test_smart_queue 2>/dev/null || true

echo "Post-test cleanup complete."
