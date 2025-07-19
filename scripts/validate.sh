#!/bin/bash
# DoS Master Framework - Installation Validation Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/dos-master-framework"
CONFIG_DIR="/etc/dos-master-framework"
LOG_DIR="/var/log/dos-master-framework"

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║             DoS Master Framework - Installation Validator       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

ISSUES=0
WARNINGS=0

# Check directories
print_info "Checking installation directories..."
if [[ -d "$INSTALL_DIR" ]]; then
    print_status "Installation directory exists: $INSTALL_DIR"
else
    print_error "Installation directory missing: $INSTALL_DIR"
    ((ISSUES++))
fi

if [[ -d "$CONFIG_DIR" ]]; then
    print_status "Configuration directory exists: $CONFIG_DIR"
else
    print_warning "Configuration directory missing: $CONFIG_DIR"
    ((WARNINGS++))
fi

if [[ -d "$LOG_DIR" ]]; then
    print_status "Log directory exists: $LOG_DIR"
else
    print_warning "Log directory missing: $LOG_DIR"
    ((WARNINGS++))
fi

# Check main files
print_info "Checking framework files..."
if [[ -d "$INSTALL_DIR/src" ]]; then
    print_status "Source directory found"
else
    print_error "Source directory missing"
    ((ISSUES++))
fi

if [[ -f "$INSTALL_DIR/src/ui/cli.py" ]]; then
    print_status "CLI module found"
else
    print_error "CLI module missing"
    ((ISSUES++))
fi

if [[ -d "$INSTALL_DIR/venv" ]]; then
    print_status "Virtual environment found"
else
    print_error "Virtual environment missing"
    ((ISSUES++))
fi

# Check commands
print_info "Checking command availability..."
if command -v dmf &> /dev/null; then
    print_status "dmf command available"
else
    print_error "dmf command not found"
    ((ISSUES++))
fi

if command -v dmf-update &> /dev/null; then
    print_status "dmf-update command available"
else
    print_warning "dmf-update command not found"
    ((WARNINGS++))
fi

# Check system tools
print_info "Checking system tools..."
TOOLS=("python3" "hping3" "nmap" "tcpdump" "curl")
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        print_status "$tool available"
    else
        print_error "$tool not found"
        ((ISSUES++))
    fi
done

# Check Python environment
print_info "Checking Python environment..."
if [[ -f "$INSTALL_DIR/venv/bin/activate" ]]; then
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_status "Python version: $PYTHON_VERSION"
    
    # Check key packages
    PACKAGES=("scapy" "flask" "psutil" "requests")
    for package in "${PACKAGES[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_status "Python package $package available"
        else
            print_error "Python package $package missing"
            ((ISSUES++))
        fi
    done
    
    deactivate
else
    print_error "Virtual environment activation script not found"
    ((ISSUES++))
fi

# Test basic functionality
print_info "Testing basic functionality..."
if timeout 30 dmf --version &>/dev/null; then
    VERSION_OUTPUT=$(dmf --version 2>&1)
    print_status "Basic functionality test passed: $VERSION_OUTPUT"
else
    print_warning "Basic functionality test failed or timed out"
    ((WARNINGS++))
fi

# Test dry-run capability
print_info "Testing dry-run capability..."
if timeout 30 dmf --target 127.0.0.1 --attack icmp_flood --duration 5 --dry-run &>/dev/null; then
    print_status "Dry-run test passed"
else
    print_warning "Dry-run test failed"
    ((WARNINGS++))
fi

# Check permissions
print_info "Checking permissions..."
if [[ -w "$LOG_DIR" ]]; then
    print_status "Log directory is writable"
else
    print_warning "Log directory is not writable"
    ((WARNINGS++))
fi

if groups $USER | grep -q wireshark; then
    print_status "User is in wireshark group"
else
    print_warning "User not in wireshark group (some features may require this)"
    ((WARNINGS++))
fi

# Summary
echo
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        Validation Summary                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

if [[ $ISSUES -eq 0 && $WARNINGS -eq 0 ]]; then
    print_status "Installation is PERFECT! All checks passed."
    echo
    echo "You can now use DoS Master Framework:"
    echo "  dmf --help                    # Show help"
    echo "  dmf --list-attacks           # List available attacks"
    echo "  dmf --target IP --attack TYPE --dry-run  # Safe testing"
elif [[ $ISSUES -eq 0 ]]; then
    print_status "Installation is GOOD with $WARNINGS warnings."
    echo
    echo "The framework should work correctly, but some features may be limited."
    echo "Consider addressing the warnings above for full functionality."
else
    print_error "Installation has $ISSUES critical issues and $WARNINGS warnings."
    echo
    echo "Please fix the critical issues before using the framework."
    if [[ $ISSUES -gt 0 ]]; then
        echo "Try running the installer again or check the installation logs."
    fi
fi

echo
echo "For help and documentation:"
echo "  dmf --help"
echo "  cat $INSTALL_DIR/docs/README.md"
echo

exit $ISSUES