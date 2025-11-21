#!/bin/bash
#
# CAsMan Service Update Script
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
    echo "  CAsMan Service Update"
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
    
    # Get actual user
    if [ -n "$SUDO_USER" ]; then
        ACTUAL_USER="$SUDO_USER"
    else
        log_error "Cannot determine user. Run with sudo."
        exit 1
    fi
    
    # Find installation directory from service file
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        log_error "Service not installed. Run install_service.sh first"
        exit 1
    fi
    
    INSTALL_DIR=$(grep "WorkingDirectory=" "$SERVICE_FILE" | cut -d= -f2)
    
    if [ -z "$INSTALL_DIR" ] || [ ! -d "$INSTALL_DIR" ]; then
        log_error "Cannot find installation directory"
        exit 1
    fi
    
    log_info "Installation directory: $INSTALL_DIR"
    
    # Stop service
    log_info "Stopping service..."
    systemctl stop "${SERVICE_NAME}.service"
    
    # Backup current installation
    BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup at: $BACKUP_DIR"
    
    # Backup only critical files
    mkdir -p "$BACKUP_DIR"
    cp -r "$INSTALL_DIR/database" "$BACKUP_DIR/" 2>/dev/null || log_warning "No database to backup"
    cp "$INSTALL_DIR/config.yaml" "$BACKUP_DIR/" 2>/dev/null || log_warning "No config to backup"
    
    # Update code (git pull if it's a git repo)
    cd "$INSTALL_DIR"
    if [ -d ".git" ]; then
        log_info "Pulling latest changes..."
        sudo -u "$ACTUAL_USER" git pull
    else
        log_warning "Not a git repository. Assuming code is already updated."
    fi
    
    # Update dependencies
    log_info "Updating dependencies..."
    sudo -u "$ACTUAL_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
    sudo -u "$ACTUAL_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet -e .
    
    # Verify installation
    if ! "$INSTALL_DIR/.venv/bin/casman" --version &> /dev/null; then
        log_error "Update failed! Rolling back..."
        
        # Restore backup
        if [ -d "$BACKUP_DIR/database" ]; then
            rm -rf "$INSTALL_DIR/database"
            cp -r "$BACKUP_DIR/database" "$INSTALL_DIR/"
        fi
        if [ -f "$BACKUP_DIR/config.yaml" ]; then
            cp "$BACKUP_DIR/config.yaml" "$INSTALL_DIR/"
        fi
        
        log_info "Backup restored. Starting service with old version..."
        systemctl start "${SERVICE_NAME}.service"
        exit 1
    fi
    
    # Restart service
    log_info "Starting updated service..."
    systemctl start "${SERVICE_NAME}.service"
    
    # Wait and check status
    sleep 2
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "Service updated and running!"
        log_info "Backup kept at: $BACKUP_DIR"
        log_info "You can remove it manually if everything works correctly"
    else
        log_error "Service failed to start after update"
        log_info "Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
        log_info "Backup available at: $BACKUP_DIR"
        exit 1
    fi
}

main "$@"
