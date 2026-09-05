#!/bin/bash
# Installation script for fan control with tachometer

set -e

echo "Installing Fan Control for Raspberry Pi (with tachometer)..."

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Install required Python packages
echo "Installing required Python packages..."
apt-get update
apt-get install -y python3-pip python3-lgpio

# Install the script
echo "Installing fan control script..."
cp fan_control.py /usr/local/bin/fan_control.py
chmod +x /usr/local/bin/fan_control.py

# Install configuration file
echo "Installing configuration file..."
cp fan_control.conf /etc/fan_control.conf

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log
touch /var/log/fan_control.log
chmod 644 /var/log/fan_control.log

# Enable GPIO kernel module for tachometer
echo "Enabling GPIO kernel modules..."
modprobe gpio-mb86s7x || true
modprobe gpio-aggregator || true

# Install systemd service
echo "Installing systemd service..."
cat > /etc/systemd/system/fan-control.service << 'EOF'
[Unit]
Description=Raspberry Pi Fan Control Service (with tachometer)
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
