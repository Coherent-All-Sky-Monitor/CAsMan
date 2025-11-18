#!/usr/bin/env python3
"""
Update coverage and test count in README.md
"""

import re
import subprocess
import sys
import os


def get_coverage():
    """Extract coverage percentage from pytest-cov output."""
    try:
        # Run pytest with coverage and capture output
        result = subprocess.run(
            ["pytest", "--cov=.", "--cov-report=term-missing", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            check=False,
        )
        output = result.stdout
        # Look for a line like: "TOTAL      123     4    97%"
        match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        if match:
            return match.group(1)
        # Fallback: look for a line like: "coverage: 97.0% of statements"
        match = re.search(r"coverage:\s+(\d+)\.\d+% of statements", output)
        if match:
            return match.group(1)
        return "0"
    except Exception:
        return "0"


def get_test_count():
    """Get total number of tests."""
    try:
        # Run pytest in collect-only mode to count tests
        result = subprocess.run(
            ["pytest", "--collect-only", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )
        # Each collected test is printed on its own line; count lines
        test_lines = [line for line in result.stdout.splitlines() if line.strip()]
        return str(len(test_lines))
    except Exception:
        return "0"


def update_readme(coverage, test_count):
    """Update README.md with new coverage and test count."""
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Update test count badge
        content = re.sub(r"tests-\d+%20passed", f"tests-{test_count}%20passed", content)

        # Update coverage badge
        content = re.sub(r"coverage-\d+\.\d+%25", f"coverage-{coverage}.0%25", content)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Updated README.md: {test_count} tests, {coverage}% coverage")
        return True
    except Exception as e:
        print(f"Error updating README.md: {e}")
        return False


if __name__ == "__main__":
    coverage = get_coverage()
    test_count = get_test_count()

    print(f"Coverage: {coverage}%")
    print(f"Tests: {test_count}")

    success = update_readme(coverage, test_count)
    sys.exit(0 if success else 1)
