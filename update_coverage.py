#!/usr/bin/env python3
"""
Update README.md with current code coverage statistics.

This script automatically generates and updates the coverage table
in the README based on current test coverage results.
"""

import re
import subprocess
import sys
from typing import Dict, List, Optional, Tuple


def get_test_count() -> Optional[int]:
    """
    Get the total number of tests that passed.

    Returns
    -------
    Optional[int]
        Number of tests passed, or None if unable to determine
    """
    try:
        # Run pytest with collection only
        result = subprocess.run(
            ["pytest", "tests/", "--co", "-q"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        # Parse output lines - each line shows "file.py: N" where N is test count
        lines = result.stdout.strip().split("\n")
        total = 0
        for line in lines:
            # Look for lines like "tests/test_file.py: 25"
            if ".py:" in line and line.strip():
                parts = line.split(":")
                if len(parts) == 2:
                    try:
                        count = int(parts[1].strip())
                        total += count
                    except ValueError:
                        continue
        
        return total if total > 0 else None
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting test count: {e}")
        return None


def get_coverage_data() -> Tuple[List[Dict], Optional[Dict]]:
    """
    Get detailed coverage data from coverage report.

    Returns
    -------
    Tuple[List[Dict], Optional[Dict]]
        A tuple containing:
        - List of module coverage data dictionaries
        - Overall coverage dictionary, or None if not available

    Each module dictionary contains:
        - name: Module name (str)
        - coverage: Coverage percentage (float)
        - covered: Number of covered lines (int)
        - total: Total number of lines (int)

    Overall dictionary contains:
        - coverage: Overall coverage percentage (float)
        - covered: Total covered lines (int)
        - total: Total lines (int)
    """
    try:
        # First, run tests with coverage to generate fresh data
        print("Running tests with coverage (this may take a minute)...")
        subprocess.run(
            ["coverage", "run", "-m", "pytest", "tests/"],
            capture_output=True,
            check=True,
        )
        print("Tests completed, generating report...")
        
        # Run coverage and get report
        result = subprocess.run(
            ["coverage", "report", "--include=casman/*"],
            capture_output=True,
            text=True,
            check=True,
        )

        lines = result.stdout.strip().split("\n")

        # Parse coverage data
        modules = []
        total_line = None

        for line in lines[2:]:  # Skip header lines
            if line.startswith("TOTAL"):
                total_line = line
                break
            if line.startswith("casman/"):
                parts = line.split()
                if len(parts) >= 4:
                    module_path = parts[0]
                    statements = int(parts[1])
                    missed = int(parts[2])
                    coverage_pct = float(parts[3].rstrip("%"))
                    covered = statements - missed

                    # Extract module name
                    module_name = module_path.replace("casman/", "").replace(".py", "")
                    if "/" in module_name:
                        module_name = module_name.replace("/", " ").title()
                    else:
                        module_name = module_name.title()

                    modules.append(
                        {
                            "name": module_name,
                            "coverage": coverage_pct,
                            "covered": covered,
                            "total": statements,
                        }
                    )

        # Parse total
        if total_line:
            parts = total_line.split()
            if len(parts) >= 4:
                total_statements = int(parts[1])
                total_missed = int(parts[2])
                total_coverage = float(parts[3].rstrip("%"))
                total_covered = total_statements - total_missed

                overall = {
                    "coverage": total_coverage,
                    "covered": total_covered,
                    "total": total_statements,
                }

                return modules, overall

        return modules, None

    except subprocess.CalledProcessError as e:
        print(f"Error running coverage: {e}")
        return [], None
    except (ValueError, IndexError) as e:
        print(f"Error parsing coverage data: {e}")
        return [], None


def update_readme_coverage() -> bool:
    """Update README.md with current coverage statistics."""
    modules, overall = get_coverage_data()

    if not modules or not overall:
        print("Could not get coverage data")
        return False

    try:
        # Read README
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Sort modules by coverage (descending)
        modules.sort(key=lambda x: x["coverage"], reverse=True)

        # Generate new table
        table_lines = [
            "| Module | Coverage | Lines Covered |",
            "|--------|----------|---------------|",
        ]

        for module in modules:
            line = (
                f"| **{module['name']}** | {module['coverage']:.1f}% | "
                f"{module['covered']}/{module['total']} |"
            )
            table_lines.append(line)

        # Add overall
        overall_line = (
            f"| **Overall** | **{overall['coverage']:.1f}%** | "
            f"**{overall['covered']}/{overall['total']}** |"
        )
        table_lines.append(overall_line)

        new_table = "\n".join(table_lines)

        # Update coverage badge
        coverage_pct = overall["coverage"]
        if coverage_pct >= 80:
            color = "green"
        elif coverage_pct >= 60:
            color = "yellow"
        else:
            color = "red"
        new_coverage_badge = (
            f"![Coverage](https://img.shields.io/badge/"
            f"coverage-{coverage_pct:.1f}%25-{color})"
        )

        # Replace coverage badge
        badge_pattern = (
            r"!\[Coverage\]\(https://img\.shields\.io/badge/"
            r"coverage-[\d\.]+%25-\w+\)"
        )
        content = re.sub(badge_pattern, new_coverage_badge, content)
        
        # Update test count badge
        test_count = get_test_count()
        if test_count:
            new_test_badge = (
                f"![Tests](https://img.shields.io/badge/"
                f"tests-{test_count}%20passed-brightgreen)"
            )
            test_badge_pattern = (
                r"!\[Tests\]\(https://img\.shields\.io/badge/"
                r"tests-\d+%20passed-\w+\)"
            )
            content = re.sub(test_badge_pattern, new_test_badge, content)
            print(f"Test badge updated: {test_count} tests")

        # Replace table
        table_start = "| Module | Coverage | Lines Covered |"
        table_end = "| **Overall**"

        start_idx = content.find(table_start)
        if start_idx != -1:
            # Find the end of the overall row
            overall_idx = content.find(table_end, start_idx)
            if overall_idx != -1:
                # Find the end of the overall line
                end_idx = content.find("|", overall_idx + len(table_end))
                end_idx = content.find("|", end_idx + 1)
                end_idx = content.find("|", end_idx + 1) + 1

                # Replace the table
                new_content = content[:start_idx] + new_table + content[end_idx:]

                # Write updated README
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_content)

                print(f"README updated with {overall['coverage']:.1f}% coverage")
                return True

        print("Could not find coverage table in README")
        return False

    except (OSError, IOError) as e:
        print(f"Error updating README: {e}")
        return False


if __name__ == "__main__":
    SUCCESS = update_readme_coverage()
    sys.exit(0 if SUCCESS else 1)
