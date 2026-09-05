#!/bin/bash
# Uninstallation script for fan control

set -e

echo "Uninstalling Fan Control..."

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo ./uninstall.sh)"
    exit 1
fi

# Stop and disable service
systemctl stop fan-control
systemctl disable fan-control

# Remove systemd service file
rm -f /etc/systemd/system/fan-control.service

# Remove script
rm -f /usr/local/bin/fan_control.py

# Remove configuration (optional, comment out to keep)
# rm -f /etc/fan_control.conf

# Remove log (optional, comment out to keep)
# rm -f /var/log/fan_control.log

# Reload systemd
systemctl daemon-reload

echo "Uninstallation complete!"
