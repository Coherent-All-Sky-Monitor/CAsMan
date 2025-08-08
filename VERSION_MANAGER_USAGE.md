# Version Manager Usage Guide

The `version_manager.py` script helps manage version numbers across the CAsMan project. It automatically updates version numbers in all relevant files and can integrate with git for tagging releases.

## Quick Start

### Show Current Versions
```bash
python version_manager.py --show
```

### Increment Version
```bash
# Patch version (0.1.0 → 0.1.1)
python version_manager.py --increment patch

# Minor version (0.1.0 → 0.2.0)
python version_manager.py --increment minor

# Major version (0.1.0 → 1.0.0)
python version_manager.py --increment major
```

### Set Specific Version
```bash
python version_manager.py --set 1.2.3
```

### Interactive Mode
```bash
python version_manager.py
# Will prompt you for the type of change and git operations
```

## Advanced Usage

### Git Integration
```bash
# Increment version and commit changes
python version_manager.py --increment minor --commit

# Increment version, commit, and create git tag
python version_manager.py --increment minor --commit --tag

# Create tag with custom message
python version_manager.py --increment major --commit --tag --tag-message "Major release with new features"
```

## Files Updated

The script automatically updates version numbers in:

1. **pyproject.toml** - Main project version
2. **casman/__init__.py** - Python package version
3. **casman/cli/utils.py** - CLI version display

## Semantic Versioning

The script follows semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR** - Breaking changes, major new features
- **MINOR** - New features, backward compatible
- **PATCH** - Bug fixes, small improvements

## Examples

```bash
# Release workflow
python version_manager.py --increment minor --commit --tag
git push origin main
git push origin --tags

# Quick patch fix
python version_manager.py --increment patch --commit

# Development version
python version_manager.py --set 1.0.0-dev
```

## Error Handling

The script will:
- Warn if files are missing
- Validate version format
- Show detailed error messages
- Prevent duplicate git tags
- Handle file permission issues gracefully

## Integration with CI/CD

You can use this script in GitHub Actions or other CI/CD systems:

```yaml
- name: Bump version
  run: |
    python version_manager.py --increment patch --commit --tag
    git push origin main --tags
```
