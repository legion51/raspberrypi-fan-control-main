#!/bin/bash
# Test script for fan control

echo "Testing Fan Control..."

# Test configuration
echo "Current configuration:"
cat /etc/fan_control.conf

# Test service status
echo -e "\nService status:"
systemctl status fan-control --no-pager

# Test manual run (dry run)
echo -e "\nTesting manual run (dry run with verbose logging):"
python3 /usr/local/bin/fan_control.py --verbose --wait-time 2 --dry-run 2>/dev/null || echo "Dry run not supported"

# Test temperature reading
echo -e "\nCurrent CPU temperature:"
cat /sys/devices/virtual/thermal/thermal_zone0/temp | awk '{print $1/1000 "°C"}'

# Test GPIO
echo -e "\nTesting GPIO access:"
python3 -c "import lgpio; h=lgpio.gpiochip_open(0); print('GPIO access OK')" 2>/dev/null || echo "GPIO access failed"

echo -e "\nTest complete!"
