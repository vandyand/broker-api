#!/bin/bash

# Broker API Local Uninstall Script
# This script removes the broker API systemd service and cleans up

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="broker-api"
SERVICE_USER="broker-api"
SERVICE_GROUP="broker-api"
INSTALL_DIR="/opt/broker-api"

echo -e "${BLUE}🗑️  Broker API Local Uninstall Script${NC}"
echo "====================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   echo "Please run without sudo and the script will prompt for sudo when needed"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    print_error "systemd is not available on this system"
    exit 1
fi

# Stop and disable the service
echo -e "\n${BLUE}🛑 Stopping service...${NC}"
if sudo systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$SERVICE_NAME"
    print_status "Service stopped"
else
    print_status "Service was not running"
fi

if sudo systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl disable "$SERVICE_NAME"
    print_status "Service disabled"
else
    print_status "Service was not enabled"
fi

# Remove systemd service file
echo -e "\n${BLUE}🔧 Removing systemd service...${NC}"
if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
    sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    sudo systemctl daemon-reload
    print_status "Systemd service file removed"
else
    print_status "Systemd service file not found"
fi

# Ask about removing installation directory
echo -e "\n${BLUE}📁 Installation directory cleanup...${NC}"
if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "${YELLOW}Installation directory found: $INSTALL_DIR${NC}"
    echo "This contains:"
    echo "  - Application files"
    echo "  - Python virtual environment"
    echo "  - Database files"
    echo "  - Configuration files"
    echo ""
    read -p "Do you want to remove the installation directory? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf "$INSTALL_DIR"
        print_status "Installation directory removed"
    else
        print_warning "Installation directory preserved at $INSTALL_DIR"
    fi
else
    print_status "Installation directory not found"
fi

# Ask about removing service user
echo -e "\n${BLUE}👤 Service user cleanup...${NC}"
if id "$SERVICE_USER" &>/dev/null; then
    echo -e "${YELLOW}Service user found: $SERVICE_USER${NC}"
    read -p "Do you want to remove the service user and group? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo userdel -r "$SERVICE_USER" 2>/dev/null || sudo userdel "$SERVICE_USER"
        sudo groupdel "$SERVICE_GROUP" 2>/dev/null || true
        print_status "Service user and group removed"
    else
        print_warning "Service user preserved: $SERVICE_USER"
    fi
else
    print_status "Service user not found"
fi

# Check for any remaining files
echo -e "\n${BLUE}🔍 Checking for remaining files...${NC}"
REMAINING_FILES=()

if [[ -d "$INSTALL_DIR" ]]; then
    REMAINING_FILES+=("$INSTALL_DIR")
fi

if id "$SERVICE_USER" &>/dev/null; then
    REMAINING_FILES+=("Service user: $SERVICE_USER")
fi

if getent group "$SERVICE_GROUP" &>/dev/null; then
    REMAINING_FILES+=("Service group: $SERVICE_GROUP")
fi

if [[ ${#REMAINING_FILES[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Remaining files/components:${NC}"
    for file in "${REMAINING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    print_warning "Some components were preserved. Remove them manually if needed."
else
    print_status "All components removed successfully"
fi

echo -e "\n${BLUE}📊 Uninstall Summary${NC}"
echo "=================="
echo "✅ Service stopped and disabled"
echo "✅ Systemd service file removed"
echo "✅ Service daemon reloaded"
echo ""

print_status "Uninstall completed!" 