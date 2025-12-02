#!/bin/bash
#
# Coverage analysis script for CAsMan
# Usage: ./coverage_check.sh
#

echo "🔍 Running coverage analysis..."
echo ""

# Run tests with coverage
coverage run -m pytest tests/

if [ $? -ne 0 ]; then
    echo "Tests failed!"
    exit 1
fi

# Generate and display coverage report
echo ""
echo "Coverage Report:"
echo "================"
coverage report --include="casman/*"

# Get overall coverage
COVERAGE=$(coverage report --include="casman/*" | tail -1 | awk '{print $4}' | sed 's/%//')
echo ""
echo "Overall Coverage: ${COVERAGE}%"

# Check threshold
MIN_COVERAGE=50
if (( $(echo "$COVERAGE < $MIN_COVERAGE" | bc -l) )); then
    echo "⚠️  Below ${MIN_COVERAGE}% threshold"
else
    echo "✅ Above ${MIN_COVERAGE}% threshold"
fi
