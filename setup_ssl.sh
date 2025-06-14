#!/usr/bin/env bash
# filepath: /var/www/crumbline/setup_ssl.sh

set -e

# Variables (modify these as needed)
DOMAIN="crumbline.example.com"
EMAIL="admin@example.com"  # For Let's Encrypt notifications

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit 1
fi

# Install Certbot
echo "Installing Certbot..."
apt update
apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
echo "Obtaining SSL certificate for $DOMAIN..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL

# Uncomment SSL configuration in Nginx config
sed -i 's/# listen 443 ssl;/listen 443 ssl;/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_certificate/ssl_certificate/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_certificate_key/ssl_certificate_key/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_protocols/ssl_protocols/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_prefer_server_ciphers/ssl_prefer_server_ciphers/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_ciphers/ssl_ciphers/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_session_cache/ssl_session_cache/' /etc/nginx/sites-available/crumbline
sed -i 's/# ssl_session_timeout/ssl_session_timeout/' /etc/nginx/sites-available/crumbline
sed -i 's/# add_header Strict-Transport-Security/add_header Strict-Transport-Security/' /etc/nginx/sites-available/crumbline

# Reload Nginx
systemctl reload nginx

echo "============================================="
echo "SSL setup complete!"
echo "Your Crumbline RSS reader is now running securely at: https://$DOMAIN"
echo "SSL certificate will auto-renew via Certbot's timer"
echo "============================================="
