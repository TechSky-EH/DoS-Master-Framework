#!/bin/bash
# DoS Master Framework Uninstall Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/dos-master-framework"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/dos-master-framework"
LOG_DIR="/var/log/dos-master-framework"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                DoS Master Framework Uninstaller                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "Please run this uninstaller as a regular user with sudo privileges"
    print_error "Do not run as root directly"
    exit 1
fi

# Confirmation
echo -e "${YELLOW}⚠️  Warning ⚠️${NC}"
echo "This will completely remove DoS Master Framework from your system."
echo "This includes:"
echo "  - Framework files from $INSTALL_DIR"
echo "  - Configuration files from $CONFIG_DIR"
echo "  - Log files from $LOG_DIR"
echo "  - Command-line tools (dmf, dmf-update)"
echo "  - System service files"
echo ""
read -p "Are you sure you want to continue? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Stop any running services
print_status "Stopping services..."
if systemctl is-active --quiet dmf-web; then
    sudo systemctl stop dmf-web
    print_status "Stopped dmf-web service"
fi

if systemctl is-enabled --quiet dmf-web; then
    sudo systemctl disable dmf-web
    print_status "Disabled dmf-web service"
fi

# Remove command-line tools
print_status "Removing command-line tools..."
if [ -f "$BIN_DIR/dmf" ]; then
    sudo rm -f "$BIN_DIR/dmf"
    print_status "Removed dmf command"
fi

if [ -f "$BIN_DIR/dmf-update" ]; then
    sudo rm -f "$BIN_DIR/dmf-update"
    print_status "Removed dmf-update command"
fi

# Remove system service
print_status "Removing system service..."
if [ -f "/etc/systemd/system/dmf-web.service" ]; then
    sudo rm -f "/etc/systemd/system/dmf-web.service"
    sudo systemctl daemon-reload
    print_status "Removed systemd service"
fi

# Remove log rotation
if [ -f "/etc/logrotate.d/dos-master-framework" ]; then
    sudo rm -f "/etc/logrotate.d/dos-master-framework"
    print_status "Removed log rotation configuration"
fi

# Remove framework files
print_status "Removing framework files..."
if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
    print_status "Removed framework directory"
fi

# Remove configuration files
print_status "Removing configuration files..."
if [ -d "$CONFIG_DIR" ]; then
    # Backup configuration before removal
    if [ "$(ls -A $CONFIG_DIR)" ]; then
        backup_dir="$HOME/dos-master-framework-config-backup-$(date +%Y%m%d_%H%M%S)"
        cp -r "$CONFIG_DIR" "$backup_dir"
        print_status "Configuration backed up to $backup_dir"
    fi
    
    sudo rm -rf "$CONFIG_DIR"
    print_status "Removed configuration directory"
fi

# Remove log files
print_status "Removing log files..."
if [ -d "$LOG_DIR" ]; then
    # Backup logs before removal
    if [ "$(ls -A $LOG_DIR)" ]; then
        backup_dir="$HOME/dos-master-framework-logs-backup-$(date +%Y%m%d_%H%M%S)"
        cp -r "$LOG_DIR" "$backup_dir"
        print_status "Logs backed up to $backup_dir"
    fi
    
    sudo rm -rf "$LOG_DIR"
    print_status "Removed log directory"
fi

# Remove user configuration
user_config_dir="$HOME/.dos-master-framework"
if [ -d "$user_config_dir" ]; then
    read -p "Remove user configuration directory ($user_config_dir)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$user_config_dir"
        print_status "Removed user configuration directory"
    fi
fi

# Remove user from wireshark group
if groups $USER | grep -q wireshark; then
    read -p "Remove user from wireshark group? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo gpasswd -d $USER wireshark
        print_status "Removed user from wireshark group"
    fi
fi

# Optional: Remove system dependencies
echo ""
read -p "Remove system dependencies (hping3, nmap, tcpdump, etc.)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Removing system dependencies..."
    
    packages_to_remove=(
        "hping3"
        "slowhttptest" 
        "siege"
    )
    
    for package in "${packages_to_remove[@]}"; do
        if dpkg -l | grep -q "^ii  $package "; then
            sudo apt remove -y "$package"
            print_status "Removed $package"
        fi
    done
    
    # Note: We don't remove nmap, tcpdump, wireshark as they might be used by other tools
    print_warning "Kept nmap, tcpdump, wireshark as they may be used by other tools"
fi

# Clean up package cache
print_status "Cleaning up..."
hash -r  # Clear command hash table

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   Uninstallation Complete!                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}DoS Master Framework has been removed from your system.${NC}"
echo ""
if [ -d "$HOME/dos-master-framework-config-backup"* ] 2>/dev/null; then
    echo -e "${BLUE}Configuration and logs have been backed up to your home directory.${NC}"
fi
echo ""
echo -e "${YELLOW}Thank you for using DoS Master Framework!${NC}"
echo -e "${YELLOW}Remember to always use security tools responsibly and legally.${NC}"