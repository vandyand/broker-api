#!/bin/bash

# Broker API Local Deployment Script
# This script sets up the broker API as a systemd service

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
SERVICE_FILE="broker-api.service"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 Broker API Local Deployment Script${NC}"
echo "=================================="

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

# Check if service file exists
if [[ ! -f "$CURRENT_DIR/$SERVICE_FILE" ]]; then
    print_error "Service file $SERVICE_FILE not found in current directory"
    exit 1
fi

print_status "System requirements check passed"

# Create service user and group
echo -e "\n${BLUE}👤 Setting up service user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$SERVICE_USER"
    print_status "Created service user: $SERVICE_USER"
else
    print_status "Service user already exists: $SERVICE_USER"
fi

# Create service group if it doesn't exist
if ! getent group "$SERVICE_GROUP" &>/dev/null; then
    sudo groupadd "$SERVICE_GROUP"
    print_status "Created service group: $SERVICE_GROUP"
fi

# Add user to group
sudo usermod -a -G "$SERVICE_GROUP" "$SERVICE_USER"
print_status "Added user to service group"

# Create installation directory
echo -e "\n${BLUE}📁 Setting up installation directory...${NC}"
sudo mkdir -p "$INSTALL_DIR"
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
print_status "Created installation directory: $INSTALL_DIR"

# Copy application files
echo -e "\n${BLUE}📦 Installing application files...${NC}"
if command -v rsync &> /dev/null; then
    sudo rsync -av --exclude='venv' --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' "$CURRENT_DIR/" "$INSTALL_DIR/"
    print_status "Copied application files using rsync"
else
    # Fallback to cp if rsync is not available
    sudo cp -r "$CURRENT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true
    sudo cp -r "$CURRENT_DIR"/.* "$INSTALL_DIR/" 2>/dev/null || true
    # Remove unwanted files
    sudo rm -rf "$INSTALL_DIR/venv" "$INSTALL_DIR/.git" "$INSTALL_DIR/__pycache__" 2>/dev/null || true
    sudo find "$INSTALL_DIR" -name "*.pyc" -delete 2>/dev/null || true
    print_status "Copied application files using cp (rsync not available)"
fi
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
print_status "Copied application files to $INSTALL_DIR"

# Create data directory
sudo mkdir -p "$INSTALL_DIR/data"
sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/data"
print_status "Created data directory"

# Set up Python virtual environment
echo -e "\n${BLUE}🐍 Setting up Python environment...${NC}"
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" python3 -m venv venv
sudo -u "$SERVICE_USER" venv/bin/pip install --upgrade pip
sudo -u "$SERVICE_USER" venv/bin/pip install -r requirements.txt
print_status "Python virtual environment created and dependencies installed"

# Initialize database
echo -e "\n${BLUE}🗄️  Initializing database...${NC}"
sudo -u "$SERVICE_USER" venv/bin/python -m app.init_db
print_status "Database initialized"

# Install systemd service
echo -e "\n${BLUE}🔧 Installing systemd service...${NC}"
sudo cp "$CURRENT_DIR/$SERVICE_FILE" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
print_status "Systemd service installed and enabled"

# Set up environment file
echo -e "\n${BLUE}⚙️  Setting up environment configuration...${NC}"
if [[ -f "$CURRENT_DIR/.env" ]]; then
    sudo cp "$CURRENT_DIR/.env" "$INSTALL_DIR/.env"
    sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/.env"
    print_status "Environment file copied from current directory"
else
    if [[ -f "$CURRENT_DIR/env.example" ]]; then
        sudo cp "$CURRENT_DIR/env.example" "$INSTALL_DIR/.env"
        sudo chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/.env"
        print_warning "Created .env file from template - please configure API credentials"
    else
        print_warning "No .env file found - please create one manually"
    fi
fi

# Start the service
echo -e "\n${BLUE}🚀 Starting service...${NC}"
sudo systemctl start "$SERVICE_NAME"
sleep 3

# Check service status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    print_status "Service started successfully"
else
    print_error "Service failed to start"
    echo "Check service status with: sudo systemctl status $SERVICE_NAME"
    echo "Check logs with: sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# Display service information
echo -e "\n${BLUE}📊 Service Information${NC}"
echo "========================"
echo "Service Name: $SERVICE_NAME"
echo "Installation Directory: $INSTALL_DIR"
echo "Service User: $SERVICE_USER"
echo "Port: 23456"
echo ""

# Show useful commands
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo "========================"
echo "Check service status: sudo systemctl status $SERVICE_NAME"
echo "View service logs: sudo journalctl -u $SERVICE_NAME -f"
echo "Restart service: sudo systemctl restart $SERVICE_NAME"
echo "Stop service: sudo systemctl stop $SERVICE_NAME"
echo "Disable service: sudo systemctl disable $SERVICE_NAME"
echo ""

# Show API endpoints
echo -e "${BLUE}🌐 API Endpoints:${NC}"
echo "=================="
echo "API Documentation: http://localhost:23456/docs"
echo "Health Check: http://localhost:23456/health"
echo "API Info: http://localhost:23456/api/v1"
echo ""

print_status "Deployment completed successfully!"
print_warning "Remember to configure your API credentials in $INSTALL_DIR/.env" 