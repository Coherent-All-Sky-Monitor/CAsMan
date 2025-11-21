#!/bin/bash
#
# CAsMan systemd Service Uninstallation Script
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVICE_NAME="casman-web"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "  CAsMan Service Uninstallation"
    echo "=========================================="
    echo ""
}

main() {
    print_header
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run with sudo or as root"
        exit 1
    fi
    
    # Check if service exists
    if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        log_warning "Service '${SERVICE_NAME}' is not installed"
        exit 0
    fi
    
    log_warning "This will remove the CAsMan systemd service"
    read -p "Are you sure? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ] && [ "$CONFIRM" != "y" ]; then
        log_info "Uninstallation cancelled"
        exit 0
    fi
    
    # Stop service
    log_info "Stopping service..."
    systemctl stop "${SERVICE_NAME}.service" || true
    
    # Disable service
    log_info "Disabling service..."
    systemctl disable "${SERVICE_NAME}.service" || true
    
    # Remove service file
    log_info "Removing service file..."
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    
    # Reload systemd
    log_info "Reloading systemd..."
    systemctl daemon-reload
    systemctl reset-failed
    
    log_success "Service uninstalled successfully"
    
    echo ""
    log_info "Note: Installation directory and databases were NOT removed"
    log_info "To remove completely, delete the CAsMan directory manually"
}

main "$@"
