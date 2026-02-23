#!/bin/bash
# FoldIt Robot - Raspberry Pi Setup Script
# Run as: sudo bash setup_pi.sh

set -euo pipefail

INSTALL_DIR="/opt/foldit"
VENV_DIR="$INSTALL_DIR/.venv"
SERVICE_FILE="/etc/systemd/system/foldit.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

log() { echo "[FoldIt] $1"; }
fail() { echo "[FoldIt ERROR] $1" >&2; exit 1; }

# 1. Check running on Raspberry Pi
log "Checking hardware..."
if ! grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
    fail "This script must be run on a Raspberry Pi (BCM processor not detected in /proc/cpuinfo)"
fi
log "Raspberry Pi detected."

# Check running as root
if [ "$EUID" -ne 0 ]; then
    fail "This script must be run as root. Use: sudo bash setup_pi.sh"
fi

# 2. Enable I2C interface
log "Enabling I2C interface..."
raspi-config nonint do_i2c 0
log "I2C enabled."

# 3. Enable camera interface
log "Enabling camera interface..."
raspi-config nonint do_camera 0
log "Camera enabled."

# 4. Install system packages
log "Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3-venv python3-pip python3-opencv libopencv-dev i2c-tools libatlas-base-dev libcap-dev libcamera-dev
log "System packages installed."

# 5. Create project directory
log "Creating project directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# 6. Copy foldit package
log "Copying foldit package..."
PACKAGE_DIR="$(dirname "$SCRIPT_DIR")"
cp -r "$PACKAGE_DIR" "$INSTALL_DIR/foldit"
chown -R pi:pi "$INSTALL_DIR"
log "Package copied."

# 7. Create virtualenv
log "Creating virtual environment..."
python3 -m venv "$VENV_DIR"
log "Virtual environment created."

# 8. Install Python dependencies
log "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet \
    opencv-python \
    numpy \
    adafruit-circuitpython-pca9685 \
    adafruit-circuitpython-motor \
    picamera2 \
    tflite-runtime \
    RPi.GPIO
chown -R pi:pi "$INSTALL_DIR"
log "Python dependencies installed."

# 9. Create systemd service
log "Creating systemd service..."
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=FoldIt Laundry Folding Robot
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/foldit
ExecStart=/opt/foldit/.venv/bin/python -m foldit.main
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
log "Systemd service created."

# 10. Enable service (don't start)
log "Enabling service..."
systemctl daemon-reload
systemctl enable foldit.service
log "Service enabled (not started)."

# 11. Hardware verification - check PCA9685 at 0x40
log "Running hardware verification..."
log "Scanning I2C bus 1..."
I2C_OUTPUT=$(i2cdetect -y 1 2>&1) || true
echo "$I2C_OUTPUT"

if echo "$I2C_OUTPUT" | grep -q "40"; then
    log "PCA9685 detected at address 0x40."
else
    log "WARNING: PCA9685 not detected at 0x40. Check wiring and connections."
fi

log ""
log "========================================="
log " FoldIt setup complete!"
log "========================================="
log ""
log " To verify hardware:  python3 $INSTALL_DIR/deploy/verify_hardware.py"
log " To start service:    sudo systemctl start foldit"
log " To check status:     sudo systemctl status foldit"
log " To view logs:        sudo journalctl -u foldit -f"
log ""
log " A reboot is recommended to apply I2C and camera changes."
