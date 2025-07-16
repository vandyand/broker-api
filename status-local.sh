#!/bin/bash

# Broker API Local Service Status Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="broker-api"
INSTALL_DIR="/opt/broker-api"

echo -e "${BLUE}📊 Broker API Local Service Status${NC}"
echo "=================================="

# Check if systemd is available
if ! command -v systemctl &> /dev/null; then
    echo -e "${RED}❌ systemd is not available on this system${NC}"
    exit 1
fi

# Check service status
echo -e "\n${BLUE}🔧 Service Status:${NC}"
if sudo systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Service is running${NC}"
    SERVICE_RUNNING=true
else
    echo -e "${RED}❌ Service is not running${NC}"
    SERVICE_RUNNING=false
fi

if sudo systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "${GREEN}✅ Service is enabled (auto-start)${NC}"
else
    echo -e "${YELLOW}⚠️  Service is not enabled${NC}"
fi

# Show detailed service status
echo -e "\n${BLUE}📋 Detailed Service Information:${NC}"
sudo systemctl status "$SERVICE_NAME" --no-pager -l

# Check installation directory
echo -e "\n${BLUE}📁 Installation Directory:${NC}"
if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "${GREEN}✅ Installation directory exists: $INSTALL_DIR${NC}"
    
    # Check key files
    if [[ -f "$INSTALL_DIR/.env" ]]; then
        echo -e "${GREEN}✅ Environment file exists${NC}"
    else
        echo -e "${YELLOW}⚠️  Environment file missing${NC}"
    fi
    
    if [[ -d "$INSTALL_DIR/venv" ]]; then
        echo -e "${GREEN}✅ Python virtual environment exists${NC}"
    else
        echo -e "${YELLOW}⚠️  Python virtual environment missing${NC}"
    fi
    
    if [[ -d "$INSTALL_DIR/data" ]]; then
        echo -e "${GREEN}✅ Data directory exists${NC}"
        # Check database file
        if [[ -f "$INSTALL_DIR/data/broker.db" ]]; then
            echo -e "${GREEN}✅ Database file exists${NC}"
        else
            echo -e "${YELLOW}⚠️  Database file missing${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Data directory missing${NC}"
    fi
else
    echo -e "${RED}❌ Installation directory missing: $INSTALL_DIR${NC}"
fi

# Check API connectivity if service is running
if [[ "$SERVICE_RUNNING" == "true" ]]; then
    echo -e "\n${BLUE}🌐 API Connectivity Test:${NC}"
    
    # Test health endpoint
    if curl -s -f "http://localhost:23456/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health endpoint responding${NC}"
    else
        echo -e "${RED}❌ Health endpoint not responding${NC}"
    fi
    
    # Test API info endpoint
    if curl -s -f "http://localhost:23456/api/v1" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API info endpoint responding${NC}"
    else
        echo -e "${RED}❌ API info endpoint not responding${NC}"
    fi
    
    echo -e "\n${BLUE}🔗 API Endpoints:${NC}"
    echo "Health Check: http://localhost:23456/health"
    echo "API Documentation: http://localhost:23456/docs"
    echo "API Info: http://localhost:23456/api/v1"
fi

# Show recent logs
echo -e "\n${BLUE}📝 Recent Service Logs (last 10 lines):${NC}"
sudo journalctl -u "$SERVICE_NAME" --no-pager -n 10

echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
echo "========================"
echo "View all logs: sudo journalctl -u $SERVICE_NAME -f"
echo "Restart service: sudo systemctl restart $SERVICE_NAME"
echo "Stop service: sudo systemctl stop $SERVICE_NAME"
echo "Start service: sudo systemctl start $SERVICE_NAME" 