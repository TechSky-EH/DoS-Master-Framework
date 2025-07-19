# DoS Master Framework

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)
![Version](https://img.shields.io/badge/version-2.0-green.svg)

**Professional DoS Testing Framework for Authorized Security Testing**

⚠️ **LEGAL WARNING**: This tool is designed for authorized security testing only. Unauthorized use against systems you do not own is illegal and may result in criminal prosecution.

## 🎯 Overview

DoS Master Framework (DMF) is a comprehensive, professional-grade Denial of Service testing framework designed for ethical hackers, penetration testers, and security professionals. It provides a complete suite of DoS attack vectors with real-time monitoring, detailed reporting, and both command-line and web interfaces.

### Key Features

- **Comprehensive Attack Suite**: ICMP floods, UDP floods, SYN floods, HTTP floods, Slowloris, and multi-vector attacks
- **Real-time Monitoring**: Live network traffic analysis and system resource monitoring
- **Professional Web Interface**: Modern, responsive web UI with real-time updates
- **Advanced Reporting**: Detailed HTML reports with graphs and metrics
- **Attack Templates**: Pre-configured attack scenarios for common testing needs
- **Safety Features**: Built-in safeguards and validation to prevent accidental misuse
- **Extensible Architecture**: Plugin system for custom attack modules

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/TechSky/dos-master-framework.git
cd dos-master-framework

# Run the installation script
chmod +x scripts/install.sh
./scripts/install.sh

# Verify installation
dmf --version