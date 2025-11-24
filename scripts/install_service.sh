#!/bin/bash
#
# CAsMan systemd Service Installation Script
# 
# This script automates the installation of CAsMan as a systemd service
# that starts on boot and restarts on failure.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration defaults
SERVICE_NAME="casman-web"
DEFAULT_PORT=5000
DEFAULT_HOST="0.0.0.0"
DEFAULT_MODE="both"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"
LOG_FILE="/tmp/casman_service_install.log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "  CAsMan systemd Service Installation"
    echo "=========================================="
    echo ""
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run with sudo or as root"
        exit 1
    fi
    
    # Check if systemd is available
    if ! command -v systemctl &> /dev/null; then
        log_error "systemd is not available on this system"
        exit 1
    fi
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version (require 3.9+)
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.9"
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        log_error "Python 3.9 or higher is required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

get_current_user_info() {
    # Get the actual user who ran sudo (not root)
    if [ -n "$SUDO_USER" ]; then
        ACTUAL_USER="$SUDO_USER"
        ACTUAL_GROUP=$(id -gn "$SUDO_USER")
    else
        ACTUAL_USER=$(whoami)
        ACTUAL_GROUP=$(id -gn)
    fi
    
    log_info "Service will run as user: $ACTUAL_USER (group: $ACTUAL_GROUP)"
}

detect_installation() {
    log_info "Detecting CAsMan installation..."
    
    # Check if already installed as a service
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        log_warning "Service '${SERVICE_NAME}' is already installed"
        read -p "Do you want to reinstall? (yes/no): " REINSTALL
        if [ "$REINSTALL" != "yes" ] && [ "$REINSTALL" != "y" ]; then
            log_info "Installation cancelled"
            exit 0
        fi
        log_info "Stopping existing service..."
        systemctl stop "${SERVICE_NAME}.service" || true
        systemctl disable "${SERVICE_NAME}.service" || true
    fi
    
    # Use current directory as installation directory
    INSTALL_DIR="$PROJECT_ROOT"
    log_info "Installation directory: $INSTALL_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "$INSTALL_DIR/.venv" ]; then
        log_warning "Virtual environment not found at $INSTALL_DIR/.venv"
        read -p "Create virtual environment now? (yes/no): " CREATE_VENV
        if [ "$CREATE_VENV" == "yes" ] || [ "$CREATE_VENV" == "y" ]; then
            create_virtual_environment
        else
            log_error "Virtual environment is required"
            exit 1
        fi
    else
        log_success "Virtual environment found"
    fi
    
    VENV_PATH="$INSTALL_DIR/.venv"
}

create_virtual_environment() {
    log_info "Creating virtual environment..."
    
    cd "$INSTALL_DIR"
    sudo -u "$ACTUAL_USER" python3 -m venv .venv
    
    log_info "Installing CAsMan in virtual environment..."
    sudo -u "$ACTUAL_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade pip
    sudo -u "$ACTUAL_USER" "$INSTALL_DIR/.venv/bin/pip" install --quiet -e .
    
    # Verify installation
    if "$INSTALL_DIR/.venv/bin/casman" --version &> /dev/null; then
        log_success "CAsMan installed successfully in virtual environment"
    else
        log_error "Failed to install CAsMan in virtual environment"
        exit 1
    fi
}

configure_service() {
    log_info "Configuring service options..."
    
    # Try to read from config.yaml first
    if read_config_yaml; then
        # Use values from config.yaml
        PORT="$CONFIG_PORT"
        HOST="$CONFIG_HOST"
        SERVICE_MODE="$CONFIG_MODE"
        SERVICE_OPTIONS="$CONFIG_OPTIONS"
        
        echo ""
        echo "Configuration from config.yaml:"
        echo "------------------------------"
        log_info "  Mode: $SERVICE_MODE"
        log_info "  Port: $PORT"
        log_info "  Host: $HOST"
        echo ""
        read -p "Use these settings? (yes/no) [yes]: " USE_CONFIG
        USE_CONFIG="${USE_CONFIG:-yes}"
        
        if [[ "$USE_CONFIG" =~ ^[Yy] ]]; then
            # Accept config.yaml values
            read -p "Enable service on boot? (yes/no) [yes]: " ENABLE_BOOT
            ENABLE_BOOT="${ENABLE_BOOT:-yes}"
            return 0
        fi
        # Fall through to manual configuration if user rejects config.yaml
    fi
    
    # Manual configuration (either no config.yaml or user rejected it)
    echo ""
    echo "Service Configuration:"
    echo "---------------------"
    
    # Service mode
    echo "Select service mode:"
    echo "  1) Both scanner and visualization (default)"
    echo "  2) Scanner only"
    echo "  3) Visualization only"
    read -p "Enter choice (1-3) [1]: " MODE_CHOICE
    
    case "${MODE_CHOICE:-1}" in
        1)
            SERVICE_MODE="both"
            SERVICE_OPTIONS=""
            ;;
        2)
            SERVICE_MODE="scanner-only"
            SERVICE_OPTIONS="--scanner-only"
            ;;
        3)
            SERVICE_MODE="visualize-only"
            SERVICE_OPTIONS="--visualize-only"
            ;;
        *)
            log_warning "Invalid choice, using default (both)"
            SERVICE_MODE="both"
            SERVICE_OPTIONS=""
            ;;
    esac
    
    # Port
    read -p "Enter port number [$DEFAULT_PORT]: " PORT
    PORT="${PORT:-$DEFAULT_PORT}"
    
    # Host
    read -p "Enter host to bind [$DEFAULT_HOST]: " HOST
    HOST="${HOST:-$DEFAULT_HOST}"
    
    # Enable on boot
    read -p "Enable service on boot? (yes/no) [yes]: " ENABLE_BOOT
    ENABLE_BOOT="${ENABLE_BOOT:-yes}"
    
    log_info "Configuration:"
    log_info "  Mode: $SERVICE_MODE"
    log_info "  Port: $PORT"
    log_info "  Host: $HOST"
    log_info "  Enable on boot: $ENABLE_BOOT"
}

read_config_yaml() {
    log_info "Reading configuration from config.yaml..."
    
    CONFIG_FILE="$INSTALL_DIR/config.yaml"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "config.yaml not found, will prompt for configuration"
        return 1
    fi
    
    # Read web app configuration from config.yaml using Python
    if command -v python3 &> /dev/null; then
        CONFIG_VALUES=$(python3 -c "
import yaml
import sys

try:
    with open('$CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    
    web_config = config.get('web_app', {})
    prod_config = web_config.get('production', {})
    
    # Get values with defaults
    port = prod_config.get('port', $DEFAULT_PORT)
    host = prod_config.get('host', '$DEFAULT_HOST')
    enable_scanner = web_config.get('enable_scanner', True)
    enable_viz = web_config.get('enable_visualization', True)
    
    # Determine mode
    if enable_scanner and enable_viz:
        mode = 'both'
        options = ''
    elif enable_scanner:
        mode = 'scanner-only'
        options = '--scanner-only'
    elif enable_viz:
        mode = 'visualize-only'
        options = '--visualize-only'
    else:
        mode = 'both'
        options = ''
    
    print(f'{port}|{host}|{mode}|{options}')
except Exception as e:
    print('', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$CONFIG_VALUES" ]; then
            IFS='|' read -r CONFIG_PORT CONFIG_HOST CONFIG_MODE CONFIG_OPTIONS <<< "$CONFIG_VALUES"
            log_success "Read configuration from config.yaml"
            log_info "  Port: $CONFIG_PORT"
            log_info "  Host: $CONFIG_HOST"
            log_info "  Mode: $CONFIG_MODE"
            return 0
        else
            log_warning "Failed to parse config.yaml, will prompt for configuration"
            return 1
        fi
    else
        log_warning "Python3 not available to parse config.yaml"
        return 1
    fi
}

verify_config_file() {
    log_info "Checking configuration file..."
    
    CONFIG_FILE="$INSTALL_DIR/config.yaml"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "config.yaml not found"
        log_info "CAsMan will use default configuration"
    else
        log_success "Using existing config.yaml"
        
        # Ensure config file is readable by the service user
        chown "$ACTUAL_USER:$ACTUAL_GROUP" "$CONFIG_FILE"
        chmod 644 "$CONFIG_FILE"
    fi
}

verify_database_permissions() {
    log_info "Checking database permissions..."
    
    DB_DIR="$INSTALL_DIR/database"
    
    if [ -d "$DB_DIR" ]; then
        # Ensure database directory and files are writable by service user
        chown -R "$ACTUAL_USER:$ACTUAL_GROUP" "$DB_DIR"
        chmod 755 "$DB_DIR"
        
        # Make database files writable
        if ls "$DB_DIR"/*.db &> /dev/null; then
            chmod 644 "$DB_DIR"/*.db
            log_success "Database permissions configured"
        fi
    else
        log_warning "Database directory not found, will be created on first run"
        mkdir -p "$DB_DIR"
        chown "$ACTUAL_USER:$ACTUAL_GROUP" "$DB_DIR"
        chmod 755 "$DB_DIR"
    fi
}

generate_service_file() {
    log_info "Generating systemd service file..."
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    TEMPLATE_FILE="$TEMPLATE_DIR/casman-web.service.template"
    
    if [ ! -f "$TEMPLATE_FILE" ]; then
        log_error "Template file not found: $TEMPLATE_FILE"
        exit 1
    fi
    
    # Replace template variables
    sed -e "s|{{USER}}|$ACTUAL_USER|g" \
        -e "s|{{GROUP}}|$ACTUAL_GROUP|g" \
        -e "s|{{WORKING_DIR}}|$INSTALL_DIR|g" \
        -e "s|{{VENV_PATH}}|$VENV_PATH|g" \
        -e "s|{{HOST}}|$HOST|g" \
        -e "s|{{PORT}}|$PORT|g" \
        -e "s|{{OPTIONS}}|$SERVICE_OPTIONS|g" \
        "$TEMPLATE_FILE" > "$SERVICE_FILE"
    
    chmod 644 "$SERVICE_FILE"
    log_success "Service file created: $SERVICE_FILE"
}

activate_service() {
    log_info "Activating service..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable if requested
    if [ "$ENABLE_BOOT" == "yes" ] || [ "$ENABLE_BOOT" == "y" ]; then
        systemctl enable "${SERVICE_NAME}.service"
        log_success "Service enabled for boot"
    fi
    
    # Start service
    log_info "Starting service..."
    systemctl start "${SERVICE_NAME}.service"
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "Service is running!"
    else
        log_error "Service failed to start"
        log_info "Checking status..."
        systemctl status "${SERVICE_NAME}.service" --no-pager || true
        log_info "Check logs with: sudo journalctl -u ${SERVICE_NAME}.service -n 50"
        exit 1
    fi
}

configure_firewall() {
    log_info "Checking firewall configuration..."
    
    read -p "Configure firewall to allow port $PORT? (yes/no) [no]: " CONFIGURE_FW
    
    if [ "$CONFIGURE_FW" == "yes" ] || [ "$CONFIGURE_FW" == "y" ]; then
        if command -v ufw &> /dev/null; then
            log_info "Configuring ufw..."
            ufw allow "$PORT/tcp"
            log_success "Firewall rule added"
        elif command -v firewall-cmd &> /dev/null; then
            log_info "Configuring firewalld..."
            firewall-cmd --permanent --add-port="$PORT/tcp"
            firewall-cmd --reload
            log_success "Firewall rule added"
        else
            log_warning "No supported firewall found (ufw or firewalld)"
        fi
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "  Installation Complete!"
    echo "=========================================="
    echo ""
    log_success "CAsMan web service has been installed and started"
    echo ""
    echo "Service Information:"
    echo "  Name: ${SERVICE_NAME}"
    echo "  User: ${ACTUAL_USER}"
    echo "  Mode: ${SERVICE_MODE}"
    echo "  URL:  http://${HOST}:${PORT}"
    echo ""
    echo "Useful Commands:"
    echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
    echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
    echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
    echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
    echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo "Configuration Files:"
    echo "  Service: /etc/systemd/system/${SERVICE_NAME}.service"
    echo "  Config:  ${INSTALL_DIR}/config.yaml"
    echo "  Database: ${INSTALL_DIR}/database/"
    echo ""
    
    if [ "$HOST" == "0.0.0.0" ]; then
        HOSTNAME=$(hostname -I | awk '{print $1}')
        echo "Access from network: http://${HOSTNAME}:${PORT}"
        echo ""
    fi
    
    log_info "Installation log saved to: $LOG_FILE"
}

# Main execution
main() {
    print_header
    
    # Initialize log
    echo "Installation started: $(date)" > "$LOG_FILE"
    
    check_prerequisites
    get_current_user_info
    detect_installation
    configure_service
    verify_config_file
    verify_database_permissions
    generate_service_file
    activate_service
    configure_firewall
    print_summary
}

# Run main function
main "$@"
