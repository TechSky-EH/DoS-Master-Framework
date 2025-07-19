#!/bin/bash
# DoS Master Framework Installation Script - FIXED VERSION

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/dos-master-framework"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/dos-master-framework"
LOG_DIR="/var/log/dos-master-framework"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                 DoS Master Framework Installer                  ║"
echo "║                    Professional DoS Testing                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}[!] Please run this installer as a regular user with sudo privileges${NC}"
    echo -e "${RED}[!] Do not run as root directly${NC}"
    exit 1
fi

# Check if sudo is available
if ! command -v sudo &> /dev/null; then
    echo -e "${RED}[!] sudo is required but not installed${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check operating system
check_os() {
    print_status "Checking operating system..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        
        case $OS in
            "Kali GNU/Linux")
                PACKAGE_MANAGER="apt"
                print_status "Detected Kali Linux - Primary platform"
                ;;
            "Ubuntu")
                PACKAGE_MANAGER="apt"
                print_status "Detected Ubuntu - Supported platform"
                ;;
            "Debian GNU/Linux")
                PACKAGE_MANAGER="apt"
                print_status "Detected Debian - Supported platform"
                ;;
            *)
                print_warning "Unsupported OS: $OS"
                print_warning "Installation may not work correctly"
                PACKAGE_MANAGER="apt"
                ;;
        esac
    else
        print_error "Cannot detect operating system"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
            print_status "Python $PYTHON_VERSION detected - OK"
        else
            print_error "Python 3.7+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found"
        exit 1
    fi
    
    # Check available disk space (need at least 500MB)
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [[ $AVAILABLE_SPACE -lt 512000 ]]; then
        print_error "Insufficient disk space. Need at least 500MB free"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &> /dev/null; then
        print_warning "No internet connectivity detected"
        print_warning "Some features may not work correctly"
    fi
}

# Install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Update package lists
    sudo $PACKAGE_MANAGER update
    
    # Essential packages
    PACKAGES=(
        "python3-pip"
        "python3-dev"
        "python3-venv"
        "hping3"
        "nmap"
        "tcpdump"
        "wireshark-common"
        "git"
        "curl"
        "build-essential"
        "libpcap-dev"
        "libnet1-dev"
    )
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing $package..."
            sudo $PACKAGE_MANAGER install -y "$package"
        else
            print_status "$package already installed"
        fi
    done
    
    # Optional packages for enhanced functionality
    OPTIONAL_PACKAGES=(
        "iftop"
        "htop"
        "glances"
        "nload"
        "siege"
        "slowhttptest"
    )
    
    for package in "${OPTIONAL_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing optional package: $package..."
            sudo $PACKAGE_MANAGER install -y "$package" || print_warning "Failed to install $package (optional)"
        fi
    done
}

# Create directories
create_directories() {
    print_status "Creating directories..."
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$CONFIG_DIR"
    sudo mkdir -p "$LOG_DIR"
    sudo mkdir -p "/opt/dos-master-framework/reports"
    
    # Set proper permissions
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$LOG_DIR"
    sudo chmod 755 "$INSTALL_DIR"
    sudo chmod 755 "$LOG_DIR"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install core dependencies
    pip install \
        scapy \
        psutil \
        pyyaml \
        requests \
        flask \
        flask-socketio \
        matplotlib \
        numpy \
        pandas \
        plotly \
        jinja2 \
        click \
        colorama \
        tqdm \
        netifaces \
        python-dateutil
    
    # Create requirements file
    pip freeze > requirements.txt
    
    deactivate
}

# Install framework files
install_framework() {
    print_status "Installing DoS Master Framework..."
    
    # Get the script directory (where install.sh is located)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # Check if we're running from the project directory
    if [[ -d "$PROJECT_ROOT/src" && -f "$PROJECT_ROOT/setup.py" ]]; then
        print_status "Installing from local project directory..."
        
        # Copy framework files
        cp -r "$PROJECT_ROOT/src" "$INSTALL_DIR/"
        
        # Copy configuration files
        if [[ -d "$PROJECT_ROOT/config" ]]; then
            cp -r "$PROJECT_ROOT/config"/* "$CONFIG_DIR/"
        fi
        
        # Copy documentation
        if [[ -d "$PROJECT_ROOT/docs" ]]; then
            cp -r "$PROJECT_ROOT/docs" "$INSTALL_DIR/"
        fi
        
        # Copy requirements if it exists
        if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
            cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/"
        fi
        
        # Copy LICENSE
        if [[ -f "$PROJECT_ROOT/LICENSE" ]]; then
            cp "$PROJECT_ROOT/LICENSE" "$INSTALL_DIR/"
        fi
        
        # Copy scripts
        if [[ -d "$PROJECT_ROOT/scripts" ]]; then
            cp -r "$PROJECT_ROOT/scripts" "$INSTALL_DIR/"
        fi
        
        print_status "Local installation completed successfully"
        
    else
        print_status "Attempting to download from GitHub..."
        
        # Try to download from GitHub
        GITHUB_URL="https://github.com/TechSky/dos-master-framework/archive/refs/heads/main.tar.gz"
        
        cd /tmp
        if curl -L -f -o dos-master-framework.tar.gz "$GITHUB_URL" 2>/dev/null; then
            # Verify the download is valid
            if file dos-master-framework.tar.gz | grep -q "gzip compressed"; then
                print_status "Download successful, extracting..."
                tar -xzf dos-master-framework.tar.gz
                
                if [[ -d "dos-master-framework-main" ]]; then
                    cp -r dos-master-framework-main/src/ "$INSTALL_DIR/"
                    [[ -d "dos-master-framework-main/config" ]] && cp -r dos-master-framework-main/config/ "$CONFIG_DIR/"
                    [[ -d "dos-master-framework-main/docs" ]] && cp -r dos-master-framework-main/docs/ "$INSTALL_DIR/"
                    [[ -f "dos-master-framework-main/requirements.txt" ]] && cp dos-master-framework-main/requirements.txt "$INSTALL_DIR/"
                    [[ -f "dos-master-framework-main/LICENSE" ]] && cp dos-master-framework-main/LICENSE "$INSTALL_DIR/"
                    
                    # Cleanup
                    rm -rf dos-master-framework*
                    print_status "GitHub installation completed successfully"
                else
                    print_error "Invalid archive structure"
                    exit 1
                fi
            else
                print_error "Downloaded file is not a valid gzip archive"
                print_error "File contents: $(head -c 50 dos-master-framework.tar.gz)"
                exit 1
            fi
        else
            print_error "Failed to download from GitHub"
            print_error "Please ensure you have internet connectivity or run from local project directory"
            exit 1
        fi
    fi
    
    # Set permissions
    chmod +x "$INSTALL_DIR/src/ui/cli.py" 2>/dev/null || true
    find "$INSTALL_DIR/src" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
}

# Create wrapper scripts
create_wrapper() {
    print_status "Creating command-line wrapper..."
    
    # Create main dmf command
    sudo tee "$BIN_DIR/dmf" > /dev/null << EOF
#!/bin/bash
# DoS Master Framework Command Wrapper

# Check if running as root for certain operations
if [[ \$EUID -eq 0 ]] && [[ "\$1" != "--web-ui" ]]; then
    echo "⚠️  Running as root - some network operations require root privileges"
fi

# Activate virtual environment and run
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR"
python3 -m src.ui.cli "\$@"
deactivate
EOF
    
    sudo chmod +x "$BIN_DIR/dmf"
    
    # Create update script
    sudo tee "$BIN_DIR/dmf-update" > /dev/null << EOF
#!/bin/bash
# DoS Master Framework Update Script

echo "Updating DoS Master Framework..."
cd "$INSTALL_DIR"

# Backup current config
cp -r "$CONFIG_DIR" "$CONFIG_DIR.backup.\$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

# Try git pull if it's a git repository
if [[ -d ".git" ]]; then
    git pull origin main 2>/dev/null || {
        echo "Git update failed, trying manual download..."
        MANUAL_UPDATE=1
    }
else
    MANUAL_UPDATE=1
fi

if [[ "\$MANUAL_UPDATE" == "1" ]]; then
    echo "Downloading latest release..."
    cd /tmp
    if curl -L -f -o dos-master-framework-update.tar.gz \\
        "https://github.com/TechSky/dos-master-framework/archive/refs/heads/main.tar.gz" 2>/dev/null; then
        
        if file dos-master-framework-update.tar.gz | grep -q "gzip compressed"; then
            tar -xzf dos-master-framework-update.tar.gz
            cp -r dos-master-framework-main/src/ "$INSTALL_DIR/"
            [[ -d "dos-master-framework-main/docs" ]] && cp -r dos-master-framework-main/docs/ "$INSTALL_DIR/"
            rm -rf dos-master-framework*
            echo "Manual update completed"
        else
            echo "Downloaded file is not valid, update failed"
            exit 1
        fi
    else
        echo "Download failed, update aborted"
        exit 1
    fi
fi

# Update Python dependencies
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade -r requirements.txt 2>/dev/null || echo "Requirements update skipped"
deactivate

echo "DoS Master Framework updated successfully"
EOF
    
    sudo chmod +x "$BIN_DIR/dmf-update"
}

# Configure system settings
configure_system() {
    print_status "Configuring system settings..."
    
    # Add user to wireshark group for packet capture
    if getent group wireshark > /dev/null 2>&1; then
        sudo usermod -a -G wireshark $USER
        print_status "Added user to wireshark group"
    fi
    
    # Configure log rotation
    sudo tee "/etc/logrotate.d/dos-master-framework" > /dev/null << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 $USER $USER
}
EOF
    
    # Create systemd service for web interface (optional)
    sudo tee "/etc/systemd/system/dmf-web.service" > /dev/null << EOF
[Unit]
Description=DoS Master Framework Web Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python -m src.ui.web
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Test command availability
    if command -v dmf &> /dev/null; then
        print_status "dmf command installed successfully"
    else
        print_error "dmf command not found in PATH"
        return 1
    fi
    
    # Test framework import
    if source "$INSTALL_DIR/venv/bin/activate" && python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); import src" 2>/dev/null; then
        print_status "Framework modules importable"
        deactivate
    else
        print_warning "Some framework modules may have import issues"
        deactivate
    fi
    
    # Test basic functionality
    if timeout 10 dmf --version &> /dev/null; then
        print_status "Basic functionality test passed"
    else
        print_warning "Basic functionality test had issues (may be normal)"
    fi
    
    # Test required tools
    TOOLS=("hping3" "nmap" "tcpdump")
    for tool in "${TOOLS[@]}"; do
        if command -v "$tool" &> /dev/null; then
            print_status "$tool available"
        else
            print_warning "$tool not found - some features may not work"
        fi
    done
    
    return 0
}

# Show post-installation information
show_post_install() {
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   Installation Completed!                       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  dmf --list-attacks           # List available attacks"
    echo "  dmf --help                   # Show help"
    echo "  dmf --web-ui                 # Start web interface"
    echo
    echo -e "${BLUE}Example Usage:${NC}"
    echo "  dmf --target 192.168.1.100 --attack icmp_flood --duration 60 --dry-run"
    echo "  dmf --target 192.168.1.100 --attack syn_flood --port 80 --monitor --dry-run"
    echo
    echo -e "${BLUE}Important Files:${NC}"
    echo "  Framework:     $INSTALL_DIR"
    echo "  Configuration: $CONFIG_DIR"
    echo "  Logs:          $LOG_DIR"
    echo "  Documentation: $INSTALL_DIR/docs"
    echo
    echo -e "${YELLOW}⚠️  Legal Notice:${NC}"
    echo -e "${YELLOW}   This tool is for authorized testing only. Unauthorized use is illegal.${NC}"
    echo -e "${YELLOW}   Always obtain written permission before testing any systems.${NC}"
    echo -e "${YELLOW}   ALWAYS use --dry-run flag first to test safely.${NC}"
    echo
    echo -e "${BLUE}Support:${NC}"
    echo "  Documentation: $INSTALL_DIR/docs/README.md"
    echo "  Run 'dmf --help' for usage information"
    echo
    
    if [[ $(groups $USER | grep -c wireshark) -eq 0 ]]; then
        echo -e "${YELLOW}Note: Log out and log back in to apply group changes${NC}"
    fi
}

# Main installation function
main() {
    echo -e "${YELLOW}⚠️  Legal Warning ⚠️${NC}"
    echo "This framework is designed for authorized security testing only."
    echo "Unauthorized use against systems you do not own is illegal."
    echo
    read -p "Do you understand and agree to use this tool responsibly? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    echo
    
    check_os
    check_requirements
    install_dependencies
    create_directories
    install_python_deps
    install_framework
    create_wrapper
    configure_system
    
    if verify_installation; then
        show_post_install
    else
        print_warning "Installation completed with some warnings"
        print_warning "The framework should still be functional"
        show_post_install
    fi
}

# Run main installation
main "$@"