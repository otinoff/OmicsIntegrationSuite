#!/bin/bash

# Script to configure Nginx for large file uploads (5GB)
# Used by GitHub Actions deploy workflow

echo "Configuring Nginx for 5GB uploads..."

# Nginx config file path
NGINX_CONFIG="/etc/nginx/sites-available/omicsintegrationsuite"
NGINX_MAIN="/etc/nginx/nginx.conf"

# Check if site config exists
if [ -f "$NGINX_CONFIG" ]; then
    echo "Found site config: $NGINX_CONFIG"

    # Check if client_max_body_size already exists
    if grep -q "client_max_body_size" "$NGINX_CONFIG"; then
        echo "Updating existing client_max_body_size..."
        sed -i 's/client_max_body_size.*;/client_max_body_size 5G;/' "$NGINX_CONFIG"
    else
        echo "Adding client_max_body_size to server block..."
        # Add after first 'server {' line
        sed -i '/server {/a\    client_max_body_size 5G;' "$NGINX_CONFIG"
    fi
else
    echo "Site config not found. Using main config: $NGINX_MAIN"

    # Update http block in main config
    if grep -q "client_max_body_size" "$NGINX_MAIN"; then
        echo "Updating existing client_max_body_size in main config..."
        sed -i 's/client_max_body_size.*;/client_max_body_size 5G;/' "$NGINX_MAIN"
    else
        echo "Adding client_max_body_size to http block..."
        sed -i '/http {/a\    client_max_body_size 5G;' "$NGINX_MAIN"
    fi
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration test passed. Reloading Nginx..."
    systemctl reload nginx || service nginx reload
    echo "✅ Nginx configured successfully for 5GB uploads!"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi
