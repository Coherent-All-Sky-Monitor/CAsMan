#!/usr/bin/env python3
"""
Update README.md with current code coverage statistics.

This script automatically generates and updates the coverage table
in the README based on current test coverage results.
"""

import subprocess
import re
import sys


def get_coverage_data():
    """Get detailed coverage data from coverage report."""
    try:
        # Run coverage and get report
        result = subprocess.run(
            ['coverage', 'report', '--include=casman/*'],
            capture_output=True, text=True, check=True
        )
        
        lines = result.stdout.strip().split('\n')
        
        # Parse coverage data
        modules = []
        total_line = None
        
        for line in lines[2:]:  # Skip header lines
            if line.startswith('TOTAL'):
                total_line = line
                break
            elif line.startswith('casman/'):
                parts = line.split()
                if len(parts) >= 4:
                    module_path = parts[0]
                    statements = int(parts[1])
                    missed = int(parts[2])
                    coverage_pct = float(parts[3].rstrip('%'))
                    covered = statements - missed
                    
                    # Extract module name
                    module_name = module_path.replace('casman/', '').replace('.py', '')
                    if '/' in module_name:
                        module_name = module_name.replace('/', ' ').title()
                    else:
                        module_name = module_name.title()
                    
                    modules.append({
                        'name': module_name,
                        'coverage': coverage_pct,
                        'covered': covered,
                        'total': statements
                    })
        
        # Parse total
        if total_line:
            parts = total_line.split()
            if len(parts) >= 4:
                total_statements = int(parts[1])
                total_missed = int(parts[2])
                total_coverage = float(parts[3].rstrip('%'))
                total_covered = total_statements - total_missed
                
                overall = {
                    'coverage': total_coverage,
                    'covered': total_covered,
                    'total': total_statements
                }
                
                return modules, overall
        
        return modules, None
        
    except subprocess.CalledProcessError as e:
        print(f"Error running coverage: {e}")
        return [], None
    except Exception as e:
        print(f"Error parsing coverage data: {e}")
        return [], None


def update_readme_coverage():
    """Update README.md with current coverage statistics."""
    modules, overall = get_coverage_data()
    
    if not modules or not overall:
        print("Could not get coverage data")
        return False
    
    try:
        # Read README
        with open('README.md', 'r') as f:
            content = f.read()
        
        # Sort modules by coverage (descending)
        modules.sort(key=lambda x: x['coverage'], reverse=True)
        
        # Generate new table
        table_lines = [
            "| Module | Coverage | Lines Covered |",
            "|--------|----------|---------------|"
        ]
        
        for module in modules:
            table_lines.append(
                f"| **{module['name']}** | {module['coverage']:.1f}% | {module['covered']}/{module['total']} |"
            )
        
        # Add overall
        table_lines.append(
            f"| **Overall** | **{overall['coverage']:.1f}%** | **{overall['covered']}/{overall['total']}** |"
        )
        
        new_table = '\n'.join(table_lines)
        
        # Update badge
        color = 'green' if overall['coverage'] >= 80 else 'yellow' if overall['coverage'] >= 60 else 'red'
        new_badge = f"![Coverage](https://img.shields.io/badge/coverage-{overall['coverage']:.1f}%25-{color})"
        
        # Replace badge
        badge_pattern = r'!\[Coverage\]\(https://img\.shields\.io/badge/coverage-[\d\.]+%25-\w+\)'
        content = re.sub(badge_pattern, new_badge, content)
        
        # Replace table
        table_start = "| Module | Coverage | Lines Covered |"
        table_end = "| **Overall**"
        
        start_idx = content.find(table_start)
        if start_idx != -1:
            # Find the end of the overall row
            overall_idx = content.find(table_end, start_idx)
            if overall_idx != -1:
                # Find the end of the overall line
                end_idx = content.find('|', overall_idx + len(table_end))
                end_idx = content.find('|', end_idx + 1)
                end_idx = content.find('|', end_idx + 1) + 1
                
                # Replace the table
                new_content = content[:start_idx] + new_table + content[end_idx:]
                
                # Write updated README
                with open('README.md', 'w') as f:
                    f.write(new_content)
                
                print(f"✅ README updated with {overall['coverage']:.1f}% coverage")
                return True
        
        print("Could not find coverage table in README")
        return False
        
    except Exception as e:
        print(f"Error updating README: {e}")
        return False


if __name__ == "__main__":
    success = update_readme_coverage()
    sys.exit(0 if success else 1)
