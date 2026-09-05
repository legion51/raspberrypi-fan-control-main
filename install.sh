#!/bin/bash
# Installation script for fan control

set -e

echo "Installing Fan Control for Raspberry Pi..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
apt-get update
apt-get install -y python3-pip python3-lgpio

# Create configuration directory
echo "Creating configuration directory..."
mkdir -p /etc/fan_control

# Install the script
echo "Installing fan control script..."
cp fan_control.py /usr/local/bin/fan_control.py
chmod +x /usr/local/bin/fan_control.py

# Install configuration file if not exists
if [ ! -f /etc/fan_control.conf ]; then
    echo "Installing default configuration..."
    cp fan_control.conf /etc/fan_control.conf
fi

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log
touch /var/log/fan_control.log
chmod 644 /var/log/fan_control.log

# Install systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/fan-control.service << 'EOF'
[Unit]
Description=Raspberry Pi Fan Control Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/fan_control.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "Enabling and starting fan control service..."
systemctl daemon-reload
systemctl enable fan-control
systemctl restart fan-control

echo "Installation complete!"
echo "Service status:"
systemctl status fan-control --no-pager
