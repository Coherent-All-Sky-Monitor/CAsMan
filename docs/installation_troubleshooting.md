# Installation Troubleshooting Guide

## Common Installation Issues and Solutions

### Issue: Import Errors After Installation

**Symptoms:**
```bash
Traceback (most recent call last):
  File "/path/to/venv/bin/casman", line 5, in <module>
    from casman.cli import main
  ModuleNotFoundError: No module named 'casman.parts'
```

**Causes:**
1. Stale installation from previous version
2. Incorrect entry points in package configuration
3. Mixed installation methods (pip vs setup.py)
4. Python path issues

**Solutions:**

#### 1. Clean Reinstallation
```bash
# Remove any existing installation
pip uninstall casman

# Clean build artifacts
make clean

# Reinstall fresh
make install-clean
```

#### 2. Verify Installation
```bash
# Run diagnostics
make troubleshoot

# Manual verification
python -c "import casman; print('✅ Package found')"
python -c "from casman.cli import main; print('✅ CLI import works')"
which casman
```

#### 3. Virtual Environment Issues
```bash
# Ensure you're in the right environment
which python
which pip

# Recreate virtual environment if needed
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Issue: Command Not Found

**Symptoms:**
```bash
$ casman
command not found: casman
```

**Solutions:**

1. **Check PATH:**
   ```bash
   echo $PATH
   which casman
   ```

2. **Reinstall with entry points:**
   ```bash
   pip install -e .
   ```

3. **Use direct python execution:**
   ```bash
   python -m casman.cli
   ```

### Issue: Permission Errors

**Symptoms:**
```bash
Permission denied: /usr/local/bin/casman
```

**Solutions:**

1. **Use virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. **User installation:**
   ```bash
   pip install --user -e .
   ```

### Development Installation

For development work, always use editable installation:

```bash
# Clone the repository
git clone https://github.com/Coherent-All-Sky-Monitor/CAsMan.git
cd CAsMan

# Switch to development branch if needed
git checkout ps/casman_upgrade

# Set up development environment
make dev-setup
```

### Testing Installation

After installation, test the basic functionality:

```bash
# Test CLI
casman --help

# Test specific commands
casman parts list
casman visualize chains

# Run full test suite
make test
```

### Getting Help

1. **Run diagnostics:**
   ```bash
   make troubleshoot
   ```

2. **Check installation:**
   ```bash
   pip show casman
   ```

3. **Verify package structure:**
   ```bash
   python -c "import casman; print(casman.__file__)"
   ls -la $(python -c "import casman; print(casman.__path__[0])")/
   ```

## Quick Fix Commands

For most installation issues, try these in order:

```bash
# 1. Quick clean reinstall
make install-clean

# 2. If that fails, nuclear option
pip uninstall casman
rm -rf *.egg-info
make clean
pip install -e .

# 3. Verify it works
make troubleshoot
casman --help
```
