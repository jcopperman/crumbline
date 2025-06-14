#!/usr/bin/env bash
# filepath: /var/www/crumbline/setup_server.sh

set -e

# Variables (modify these as needed)
DOMAIN="crumbline.example.com"
APP_PATH="/var/www/crumbline"
ADMIN_USER="admin"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="changeme123"  # Change this!

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Install dependencies
echo "Installing system dependencies..."
apt update
apt install -y python3 python3-venv python3-pip nginx supervisor

# Create a Python virtual environment if it doesn't exist
if [ ! -d "$APP_PATH/venv" ]; then
    echo "Creating Python virtual environment..."
    cd $APP_PATH
    python3 -m venv venv
    
    echo "Installing Python dependencies..."
    $APP_PATH/venv/bin/pip install -r requirements.txt
fi

# Create admin user
echo "Creating admin user..."
cd $APP_PATH
$APP_PATH/venv/bin/python create_admin.py $ADMIN_USER $ADMIN_EMAIL $ADMIN_PASSWORD

# Setup systemd service
echo "Setting up systemd service..."
cp $APP_PATH/crumbline.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable crumbline.service
systemctl start crumbline.service

# Setup Nginx
echo "Setting up Nginx..."
cp $APP_PATH/nginx_crumbline.conf /etc/nginx/sites-available/crumbline
ln -sf /etc/nginx/sites-available/crumbline /etc/nginx/sites-enabled/
sed -i "s/crumbline.example.com/$DOMAIN/g" /etc/nginx/sites-available/crumbline

# Set proper permissions
echo "Setting file permissions..."
chown -R www-data:www-data $APP_PATH
chmod -R 755 $APP_PATH

# Test Nginx configuration
nginx -t

# Restart Nginx
echo "Restarting Nginx..."
systemctl restart nginx

echo "============================================="
echo "Setup complete!"
echo "Your Crumbline RSS reader is now running at: http://$DOMAIN"
echo "Login with: $ADMIN_USER / $ADMIN_PASSWORD"
echo "Remember to change the default password!"
echo "============================================="
