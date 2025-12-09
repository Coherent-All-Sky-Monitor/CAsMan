#!/bin/bash
#
# CAsMan Environment Setup Script
#
# This script activates the virtual environment and loads R2 credentials.
# Usage: source scripts/setup_env.sh
#

# Get script directory and project root
# Handle both sourcing and direct execution
if [ -n "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Setting up CAsMan environment..."

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${RED}❌ Virtual environment not found at $PROJECT_ROOT/.venv${NC}"
    echo "Run 'make install' first to create the virtual environment"
    return 1 2>/dev/null || exit 1
fi

# Activate virtual environment
echo -e "${GREEN}✓${NC} Activating virtual environment..."
source "$PROJECT_ROOT/.venv/bin/activate"

# Load R2 credentials if they exist
if [ -f "$HOME/.casman/r2_credentials.env" ]; then
    echo -e "${GREEN}✓${NC} Loading R2 credentials from ~/.casman/r2_credentials.env"
    source "$HOME/.casman/r2_credentials.env"
else
    echo -e "${YELLOW}⚠${NC}  R2 credentials not found at ~/.casman/r2_credentials.env"
    echo ""
    echo "To set up R2 credentials, create the file with:"
    echo "  mkdir -p ~/.casman"
    echo "  cat > ~/.casman/r2_credentials.env <<EOF"
    echo "export R2_ACCOUNT_ID=\"your-account-id\""
    echo "export R2_ACCESS_KEY_ID=\"your-access-key-id\""
    echo "export R2_SECRET_ACCESS_KEY=\"your-secret-access-key\""
    echo "EOF"
    echo "  chmod 600 ~/.casman/r2_credentials.env"
    echo ""
fi

# Verify activation
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✓${NC} Environment ready!"
    echo "  Python: $(which python)"
    echo "  Virtual env: $VIRTUAL_ENV"
    
    # Check if R2 credentials are set
    if [ -n "$R2_ACCESS_KEY_ID" ]; then
        echo -e "${GREEN}✓${NC} R2 credentials loaded"
    fi
else
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    return 1 2>/dev/null || exit 1
fi
