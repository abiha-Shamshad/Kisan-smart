#!/bin/bash

# Kisan Smart - Production Deployment Script
# Target: Ubuntu 24.04 LTS
# Usage: ./deploy.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

LOG_FILE="deploy.log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root"
fi

log "Starting Kisan Smart deployment..."

# 1. Update System
log "Updating system packages..."
apt update && apt upgrade -y || error "Failed to update system"

# 2. Install Dependencies
log "Installing dependencies..."
apt install -y python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib libpq-dev \
    nginx \
    supervisor \
    redis-server \
    git curl ufw fail2ban \
    build-essential || error "Failed to install dependencies"

# 3. Configure Firewall
log "Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
# ufw enable  # Uncomment to enable automatically (risk of locking out if SSH not allowed)
warn "Firewall rules updated. Please enable UFW manually if not active."

# 4. Create User
APP_USER="kisansmart"
APP_DIR="/home/$APP_USER/kisan-smart"

if id "$APP_USER" &>/dev/null; then
    warn "User $APP_USER already exists"
else
    log "Creating application user..."
    adduser --disabled-password --gecos "" "$APP_USER"
    usermod -aG sudo "$APP_USER"
fi

# 5. Database Setup
log "Setting up PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql
warn "Please create PostgreSQL database and user manually:"
warn "  sudo -u postgres psql"
warn "  CREATE DATABASE kisan_smart;"
warn "  CREATE USER kisansmart WITH PASSWORD 'your_password';"
warn "  GRANT ALL PRIVILEGES ON DATABASE kisan_smart TO kisansmart;"

# 6. Application Setup
log "Setting up application directory..."
if [ -d "$APP_DIR" ]; then
    warn "Directory exists. Pulling latest changes..."
    cd "$APP_DIR"
    # git pull origin main
else
    log "Cloning repository..."
    # git clone https://github.com/yourusername/kisan-smart.git "$APP_DIR"
    mkdir -p "$APP_DIR"
    # Copy files here in real scenario
fi

# Fix permissions
chown -R "$APP_USER:$APP_USER" "/home/$APP_USER"

# 7. Python Environment
log "Setting up Python virtual environment..."
su - "$APP_USER" -c "cd $APP_DIR && python3 -m venv venv"
su - "$APP_USER" -c "cd $APP_DIR && source venv/bin/activate && pip install --upgrade pip"
su - "$APP_USER" -c "cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"
su - "$APP_USER" -c "cd $APP_DIR && source venv/bin/activate && pip install gunicorn gevent"

# 8. Logs Directory
mkdir -p /var/log/kisansmart
chown -R "$APP_USER:$APP_USER" /var/log/kisansmart

log "Deployment preparation complete!"
log "Next steps:"
log "1. Configure .env file in $APP_DIR"
log "2. Initialize database (flask db upgrade)"
log "3. Configure Nginx and Supervisor using provided config files"
log "4. Set up SSL with Let's Encrypt"
