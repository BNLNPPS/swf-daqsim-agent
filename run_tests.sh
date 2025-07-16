#!/bin/bash
set -e

# Print a single 100-character line of '*' between two blank lines as the first output
printf "\n%100s\n\n" | tr ' ' '*'

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if a virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Error: No Python virtual environment is active"
    echo "   Please activate the swf-testbed virtual environment first:"
    echo "   cd swf-testbed && source .venv/bin/activate"
    exit 1
fi

echo "Using Python environment: $VIRTUAL_ENV"

# Run tests if the tests directory exists and is not empty
if [ -d "$SCRIPT_DIR/tests" ] && [ "$(ls -A "$SCRIPT_DIR/tests" 2>/dev/null)" ]; then
    echo "Running pytest for swf-daqsim-agent..."
    pytest tests
else
    echo "[SKIP] No tests/ directory found in swf-daqsim-agent. Skipping."
fi