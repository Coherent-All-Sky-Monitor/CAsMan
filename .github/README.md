# Documentation Automation

This directory contains automation tools for keeping CAsMan documentation up-to-date.

## 🤖 Automated Updates

### GitHub Actions (CI/CD)

The project includes GitHub Actions that automatically update documentation when:
- Code is pushed to `main` or `develop` branches
- Pull requests are opened that modify Python files
- The documentation generator is updated

**Workflow:** `.github/workflows/update-docs.yml`

**What it does:**
- Generates fresh API documentation from source code
- Updates test count and coverage badges in README.md
- Commits changes back to the repository
- Creates PRs for documentation updates when appropriate

### Local Development

#### Make Targets

```bash
# Update documentation and coverage info
make update-docs

# Generate documentation only
make docs

# Set up pre-commit hooks for automatic updates
make setup-hooks

# Complete development setup
make dev-setup
```

#### Pre-commit Hook

Install the pre-commit hook to automatically update documentation before commits:

```bash
make setup-hooks
```

This will:
- Update documentation when Python files change
- Update coverage statistics
- Stage updated documentation files

#### Manual Updates

```bash
# Generate documentation
cd docs && python generate_docs.py

# Update coverage info
python .github/scripts/update_coverage.py
```

## 📁 Files

- `workflows/update-docs.yml` - GitHub Actions workflow
- `scripts/update_coverage.py` - Coverage and test count updater
- `hooks/pre-commit` - Git pre-commit hook
- `../docs/generate_docs.py` - Documentation generator
- `../Makefile` - Development automation

## 🔧 Configuration

The automation is configured to:
- Monitor changes in `casman/` (Python source)
- Update documentation in `docs/`
- Update badges in `README.md`
- Respect git workflow (staging, committing)

## 📚 Generated Documentation

The following files are automatically generated/updated:

- `docs/api_reference.md` - Complete API reference
- `docs/assembly.md` - Assembly package documentation  
- `docs/parts.md` - Parts package documentation
- `docs/database.md` - Database package documentation
- `docs/visualization.md` - Visualization package documentation
- `docs/config.md` - Configuration package documentation
- `docs/cli.md` - CLI package documentation
- `README.md` - Test count and coverage badges

## 🚀 Usage in Development

1. **Make changes to Python code**
2. **Commit normally** - docs update automatically with pre-commit hook
3. **Push changes** - GitHub Actions updates docs on remote
4. **Review generated docs** - Check that documentation reflects your changes

## 🎯 Best Practices

- **Enable pre-commit hooks** for immediate feedback
- **Review auto-generated docs** before pushing
- **Update docstrings** when adding new functions/classes
- **Run `make update-docs`** before releases
- **Check CI status** to ensure documentation builds succeed

This automation ensures documentation stays current with minimal manual effort! 🎉
