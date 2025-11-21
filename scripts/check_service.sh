#!/bin/bash
#
# CAsMan Service Health Check Script
#

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
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "  CAsMan Service Health Check"
    echo "=========================================="
    echo ""
}

check_service_status() {
    echo "Service Status:"
    echo "---------------"
    
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log_success "Service is running"
    else
        log_error "Service is not running"
        return 1
    fi
    
    if systemctl is-enabled --quiet "${SERVICE_NAME}.service"; then
        log_success "Service is enabled (starts on boot)"
    else
        log_warning "Service is not enabled"
    fi
    
    echo ""
}

check_port() {
    echo "Port Check:"
    echo "-----------"
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        log_error "Service file not found"
        return 1
    fi
    
    PORT=$(grep "ExecStart=" "$SERVICE_FILE" | grep -oP '(?<=--port )[0-9]+')
    
    if [ -z "$PORT" ]; then
        log_warning "Cannot determine port"
        echo ""
        return
    fi
    
    if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        log_success "Port $PORT is listening"
    elif ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
        log_success "Port $PORT is listening"
    else
        log_error "Port $PORT is not listening"
    fi
    
    echo ""
}

check_http_endpoint() {
    echo "HTTP Endpoint Check:"
    echo "--------------------"
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    PORT=$(grep "ExecStart=" "$SERVICE_FILE" | grep -oP '(?<=--port )[0-9]+')
    
    if [ -z "$PORT" ]; then
        log_warning "Cannot determine port, skipping HTTP check"
        echo ""
        return
    fi
    
    if command -v curl &> /dev/null; then
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT" | grep -q "200\|301\|302"; then
            log_success "HTTP endpoint responding"
        else
            log_error "HTTP endpoint not responding"
        fi
    else
        log_warning "curl not installed, skipping HTTP check"
    fi
    
    echo ""
}

check_recent_errors() {
    echo "Recent Errors (last 10):"
    echo "------------------------"
    
    ERRORS=$(journalctl -u "${SERVICE_NAME}.service" -p err -n 10 --no-pager 2>/dev/null)
    
    if [ -z "$ERRORS" ]; then
        log_success "No recent errors"
    else
        log_warning "Recent errors found:"
        echo "$ERRORS"
    fi
    
    echo ""
}

show_service_info() {
    echo "Service Information:"
    echo "--------------------"
    
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ -f "$SERVICE_FILE" ]; then
        echo "User:    $(grep "^User=" "$SERVICE_FILE" | cut -d= -f2)"
        echo "WorkDir: $(grep "^WorkingDirectory=" "$SERVICE_FILE" | cut -d= -f2)"
        
        PORT=$(grep "ExecStart=" "$SERVICE_FILE" | grep -oP '(?<=--port )[0-9]+')
        echo "Port:    ${PORT:-unknown}"
        
        if grep -q "scanner-only" "$SERVICE_FILE"; then
            echo "Mode:    Scanner only"
        elif grep -q "visualize-only" "$SERVICE_FILE"; then
            echo "Mode:    Visualization only"
        else
            echo "Mode:    Both"
        fi
    fi
    
    echo ""
}

show_useful_commands() {
    echo "Useful Commands:"
    echo "----------------"
    echo "  View status:  sudo systemctl status ${SERVICE_NAME}"
    echo "  View logs:    sudo journalctl -u ${SERVICE_NAME} -f"
    echo "  Restart:      sudo systemctl restart ${SERVICE_NAME}"
    echo "  Stop:         sudo systemctl stop ${SERVICE_NAME}"
    echo "  Start:        sudo systemctl start ${SERVICE_NAME}"
    echo ""
}

main() {
    print_header
    check_service_status
    check_port
    check_http_endpoint
    check_recent_errors
    show_service_info
    show_useful_commands
}

main "$@"
