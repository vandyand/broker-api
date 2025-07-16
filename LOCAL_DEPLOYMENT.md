# Local Systemd Deployment Guide

This guide covers deploying the Broker API as a systemd service on Linux systems for production use.

## Overview

The local deployment option provides:
- **Systemd service management** - Automatic startup, restart, and monitoring
- **Dedicated service user** - Secure isolation with `broker-api` user
- **Production-ready configuration** - Proper logging, security settings, and resource limits
- **Easy management** - Simple scripts for deployment, status checking, and removal

## Prerequisites

- Linux system with systemd
- Python 3.11+
- sudo privileges
- rsync (for file deployment)

## Quick Deployment

### 1. Deploy the Service

```bash
./deploy-local.sh
```

This script will:
- Create a dedicated `broker-api` user and group
- Install the application to `/opt/broker-api`
- Set up a Python virtual environment
- Initialize the database
- Install and enable the systemd service
- Start the service automatically

### 2. Verify Deployment

```bash
./status-local.sh
```

This will show:
- Service status (running/stopped)
- Installation directory status
- API connectivity test
- Recent service logs

### 3. Access the API

- **API Documentation**: http://localhost:23456/docs
- **Health Check**: http://localhost:23456/health
- **API Info**: http://localhost:23456/api/v1

## Service Management

### Basic Commands

```bash
# Check service status
sudo systemctl status broker-api

# Start the service
sudo systemctl start broker-api

# Stop the service
sudo systemctl stop broker-api

# Restart the service
sudo systemctl restart broker-api

# Enable auto-start on boot
sudo systemctl enable broker-api

# Disable auto-start on boot
sudo systemctl disable broker-api
```

### Logging

```bash
# View real-time logs
sudo journalctl -u broker-api -f

# View recent logs (last 50 lines)
sudo journalctl -u broker-api -n 50

# View logs since boot
sudo journalctl -u broker-api -b

# View logs for specific time period
sudo journalctl -u broker-api --since "2024-01-01 00:00:00" --until "2024-01-02 00:00:00"
```

### Configuration

The service configuration is located at:
- **Service file**: `/etc/systemd/system/broker-api.service`
- **Application directory**: `/opt/broker-api`
- **Environment file**: `/opt/broker-api/.env`
- **Database**: `/opt/broker-api/data/broker.db`

### Environment Configuration

Edit the environment file to configure API credentials:

```bash
sudo nano /opt/broker-api/.env
```

Required configuration:
```env
# OANDA API (Forex)
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
OANDA_ENVIRONMENT=practice

# Bitunix API (Crypto)
BITUNIX_API_KEY=your_bitunix_api_key
BITUNIX_SECRET_KEY=your_bitunix_secret_key

# Database
DATABASE_URL=sqlite:///./data/broker.db

# Logging
LOG_LEVEL=INFO
```

After changing the environment file, restart the service:

```bash
sudo systemctl restart broker-api
```

## Security Features

The systemd service includes several security features:

- **Dedicated user**: Runs as `broker-api` user (not root)
- **File system protection**: `ProtectSystem=strict` prevents access to system files
- **Home directory protection**: `ProtectHome=true` prevents access to user home directories
- **No new privileges**: `NoNewPrivileges=true` prevents privilege escalation
- **Private temp directory**: `PrivateTmp=true` isolates temporary files
- **Resource limits**: File descriptor and process limits

## Troubleshooting

### Service Won't Start

1. Check service status:
```bash
sudo systemctl status broker-api
```

2. View detailed logs:
```bash
sudo journalctl -u broker-api -n 50
```

3. Common issues:
   - Missing API credentials in `.env` file
   - Port 23456 already in use
   - Permission issues with `/opt/broker-api` directory
   - Python virtual environment not properly set up

### API Not Responding

1. Check if service is running:
```bash
sudo systemctl is-active broker-api
```

2. Test API connectivity:
```bash
curl http://localhost:23456/health
```

3. Check firewall settings:
```bash
sudo ufw status
# If firewall is active, allow port 23456:
sudo ufw allow 23456
```

### Database Issues

1. Check database file permissions:
```bash
ls -la /opt/broker-api/data/
```

2. Reinitialize database if needed:
```bash
sudo -u broker-api /opt/broker-api/venv/bin/python -m app.init_db
```

## Uninstallation

To completely remove the service:

```bash
./uninstall-local.sh
```

This script will:
- Stop and disable the service
- Remove the systemd service file
- Optionally remove the installation directory
- Optionally remove the service user and group

## Performance Tuning

### Resource Limits

The service includes default resource limits. To adjust them, edit the service file:

```bash
sudo systemctl edit broker-api
```

Add custom limits:
```ini
[Service]
LimitNOFILE=131072
LimitNPROC=8192
```

### Logging Configuration

To adjust logging verbosity, modify the environment file:

```env
LOG_LEVEL=DEBUG  # For detailed logging
LOG_LEVEL=WARNING  # For minimal logging
```

## Monitoring

### Health Checks

The service provides health check endpoints:

```bash
# Basic health check
curl http://localhost:23456/health

# API information
curl http://localhost:23456/api/v1
```

### System Monitoring

Monitor system resources:

```bash
# Check memory usage
ps aux | grep broker-api

# Check disk usage
du -sh /opt/broker-api/

# Check open file descriptors
lsof -p $(pgrep -f broker-api)
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
sudo cp /opt/broker-api/data/broker.db /backup/broker-$(date +%Y%m%d).db

# Restore from backup
sudo systemctl stop broker-api
sudo cp /backup/broker-20240101.db /opt/broker-api/data/broker.db
sudo chown broker-api:broker-api /opt/broker-api/data/broker.db
sudo systemctl start broker-api
```

### Configuration Backup

```bash
# Backup configuration
sudo cp /opt/broker-api/.env /backup/env-$(date +%Y%m%d)

# Backup service file
sudo cp /etc/systemd/system/broker-api.service /backup/service-$(date +%Y%m%d)
```

## Support

For issues with the local deployment:

1. Check the troubleshooting section above
2. Review service logs: `sudo journalctl -u broker-api -f`
3. Verify system requirements and dependencies
4. Check file permissions and ownership

The local deployment provides a production-ready setup that's easy to manage and monitor while maintaining security best practices. 