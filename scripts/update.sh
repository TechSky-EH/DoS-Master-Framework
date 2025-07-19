#!/bin/bash
# DoS Master Framework Update Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_DIR="/opt/dos-master-framework"
CONFIG_DIR="/etc/dos-master-framework"
BACKUP_DIR="$HOME/.dos-master-framework/backups"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                DoS Master Framework Updater                     ║"
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

# Check if framework is installed
if [ ! -d "$INSTALL_DIR" ]; then
    print_error "DoS Master Framework is not installed"
    print_error "Please run the installer first"
    exit 1
fi

# Check for internet connectivity
if ! ping -c 1 google.com &> /dev/null; then
    print_error "No internet connection available"
    print_error "Cannot download updates"
    exit 1
fi

# Get current version
current_version="unknown"
if [ -f "$INSTALL_DIR/src/__init__.py" ]; then
    current_version=$(grep "__version__" "$INSTALL_DIR/src/__init__.py" | cut -d"'" -f2)
fi

print_status "Current version: $current_version"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current installation
print_status "Creating backup..."
backup_name="dmf_backup_$(date +%Y%m%d_%H%M%S)"
backup_path="$BACKUP_DIR/$backup_name"

# Backup framework files
cp -r "$INSTALL_DIR" "$backup_path"

# Backup configuration
if [ -d "$CONFIG_DIR" ]; then
    cp -r "$CONFIG_DIR" "$backup_path/config_backup"
fi

print_status "Backup created: $backup_path"

# Stop any running services
if systemctl is-active --quiet dmf-web; then
    print_status "Stopping dmf-web service..."
    sudo systemctl stop dmf-web
fi

# Download latest version
print_status "Downloading latest version..."
cd /tmp

# Try git pull if it's a git repository
if [ -d "$INSTALL_DIR/.git" ]; then
    print_status "Updating from git repository..."
    cd "$INSTALL_DIR"
    git pull origin main
    update_success=$?
else
    # Download from GitHub releases
    print_status "Downloading from GitHub..."
    curl -L -o dos-master-framework-update.tar.gz \
        "https://github.com/TechSky/dos-master-framework/archive/main.tar.gz"
    
    if [ $? -eq 0 ]; then
        # Extract and update
        tar -xzf dos-master-framework-update.tar.gz
        
        # Update framework files
        sudo cp -r dos-master-framework-main/src/* "$INSTALL_DIR/src/"
        sudo cp -r dos-master-framework-main/scripts/* "$INSTALL_DIR/scripts/"
        
        # Update documentation
        if [ -d "dos-master-framework-main/docs" ]; then
            sudo cp -r dos-master-framework-main/docs/* "$INSTALL_DIR/docs/"
        fi
        
        # Update requirements
        sudo cp dos-master-framework-main/requirements.txt "$INSTALL_DIR/"
        
        # Cleanup
        rm -rf dos-master-framework-main dos-master-framework-update.tar.gz
        
        update_success=0
    else
        update_success=1
    fi
fi

if [ $update_success -ne 0 ]; then
    print_error "Failed to download updates"
    print_error "Restoring from backup..."
    
    # Restore from backup
    sudo rm -rf "$INSTALL_DIR"
    sudo cp -r "$backup_path" "$INSTALL_DIR"
    
    exit 1
fi

# Update Python dependencies
print_status "Updating Python dependencies..."
cd "$INSTALL_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install --upgrade -r requirements.txt
    deactivate
else
    print_warning "Virtual environment not found, creating new one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
fi

# Update configuration files (merge, don't overwrite)
print_status "Updating configuration..."

# Check for new configuration options
if [ -f "config/default.yaml" ] && [ -f "$CONFIG_DIR/default.yaml" ]; then
    # Simple merge - copy new file with timestamp and let user merge manually
    sudo cp "config/default.yaml" "$CONFIG_DIR/default.yaml.new"
    print_status "New configuration template saved as default.yaml.new"
    print_status "Please review and merge any new options manually"
fi

# Set proper permissions
sudo chown -R $USER:$USER "$INSTALL_DIR"
sudo chmod +x "$INSTALL_DIR/src/ui/cli.py"

# Update command wrapper if needed
if [ -f "scripts/install.sh" ]; then
    # Extract wrapper creation from install script
    print_status "Updating command wrapper..."
    
    sudo tee "/usr/local/bin/dmf" > /dev/null << EOF
#!/bin/bash
# DoS Master Framework Command Wrapper

if [[ \$EUID -eq 0 ]] && [[ "\$1" != "--web-ui" ]]; then
    echo "⚠️  Running as root - some network operations require root privileges"
fi

source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
python3 -m src.ui.cli "\$@"
deactivate
EOF
    
    sudo chmod +x "/usr/local/bin/dmf"
fi

# Get new version
new_version="unknown"
if [ -f "$INSTALL_DIR/src/__init__.py" ]; then
    new_version=$(grep "__version__" "$INSTALL_DIR/src/__init__.py" | cut -d"'" -f2)
fi

# Restart services if they were running
if systemctl is-enabled --quiet dmf-web; then
    print_status "Restarting dmf-web service..."
    sudo systemctl start dmf-web
fi

# Verify installation
print_status "Verifying update..."
if dmf --version &> /dev/null; then
    print_status "Update verification successful"
else
    print_error "Update verification failed"
    print_error "Restoring from backup..."
    
    sudo rm -rf "$INSTALL_DIR"
    sudo cp -r "$backup_path" "$INSTALL_DIR"
    exit 1
fi

# Clean up old backups (keep last 5)
print_status "Cleaning up old backups..."
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs -r rm -rf

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                     Update Complete!                            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}DoS Master Framework has been updated successfully!${NC}"
echo ""
echo -e "${BLUE}Version Information:${NC}"
echo "  Previous: $current_version"
echo "  Current:  $new_version"
echo ""
echo -e "${BLUE}Backup Location:${NC}"
echo "  $backup_path"
echo ""
echo -e "${YELLOW}If you encounter any issues, you can restore from the backup:${NC}"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo cp -r $backup_path $INSTALL_DIR"