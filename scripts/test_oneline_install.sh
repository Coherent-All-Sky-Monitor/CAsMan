#!/bin/bash
# Test script to verify one-line antenna module installation

echo "Testing one-line antenna module installation..."
echo ""

# Create temporary virtual environment
TEMP_VENV=$(mktemp -d)/test_venv
python3 -m venv "$TEMP_VENV"

# Activate venv
source "$TEMP_VENV/bin/activate"

echo "Installing antenna module from GitHub..."
pip install -q "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"

if [ $? -eq 0 ]; then
    echo "✓ Installation successful"
    echo ""
    echo "Testing import..."
    python3 << EOF
try:
    from casman.antenna import AntennaArray, AntennaPosition
    from casman.antenna.grid import parse_grid_code, AntennaGridPosition
    print("✓ All antenna module imports successful")
    print("")
    print("Available classes:")
    print("  - AntennaArray")
    print("  - AntennaPosition")
    print("  - AntennaGridPosition")
    print("")
    print("Checking dependencies...")
    import yaml
    print("  ✓ PyYAML installed")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)
EOF
else
    echo "✗ Installation failed"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Cleanup
deactivate
rm -rf "$TEMP_VENV"

echo ""
echo "✓ One-line install test passed!"
echo ""
echo "To install yourself, run:"
echo '  pip install "git+https://github.com/Coherent-All-Sky-Monitor/CAsMan.git#egg=casman[antenna]"'
