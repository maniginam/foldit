# FoldIt Robot - Deployment Guide

## Prerequisites

- Raspberry Pi 4 (2GB+ RAM) with Raspberry Pi OS (Bookworm or later)
- PCA9685 16-channel servo driver connected via I2C (SDA/SCL to GPIO 2/3)
- 6 servo motors connected to PCA9685 channels 0-5
- Pi Camera Module v2 or compatible (connected via CSI ribbon cable)
- 5V power supply for servos (do NOT power servos from Pi GPIO)
- SSH access or direct terminal on the Pi

## Deployment Steps

### 1. Transfer the project to the Pi

```bash
# From your development machine
scp -r foldit/ pi@<pi-ip>:~/foldit/
```

### 2. Run the setup script

```bash
ssh pi@<pi-ip>
cd ~/foldit/deploy
sudo bash setup_pi.sh
```

The script will:
- Verify it's running on a Raspberry Pi
- Enable I2C and camera interfaces
- Install system dependencies
- Create `/opt/foldit/` with a Python virtualenv
- Install Python packages
- Create and enable a systemd service
- Scan I2C bus for the PCA9685

### 3. Reboot

```bash
sudo reboot
```

A reboot is required to apply I2C and camera interface changes.

### 4. Verify hardware

```bash
cd /opt/foldit
sudo python3 deploy/verify_hardware.py
```

This tests I2C detection, servo sweep on all channels, and camera capture.

## Starting the Service

```bash
# Start
sudo systemctl start foldit

# Stop
sudo systemctl stop foldit

# Restart
sudo systemctl restart foldit

# Check status
sudo systemctl status foldit

# View live logs
sudo journalctl -u foldit -f

# View recent logs
sudo journalctl -u foldit --since "10 minutes ago"
```

## Troubleshooting

### I2C not detected / PCA9685 not found at 0x40

1. Check wiring: SDA to GPIO 2 (pin 3), SCL to GPIO 3 (pin 5), GND to GND
2. Verify I2C is enabled:
   ```bash
   sudo raspi-config nonint get_i2c  # Returns 0 if enabled
   ```
3. Scan the bus manually:
   ```bash
   sudo i2cdetect -y 1
   ```
4. Check for address conflicts — PCA9685 default is 0x40
5. Ensure pull-up resistors are present (most breakout boards include them)

### Camera not found

1. Check the ribbon cable is seated firmly at both ends
2. Verify camera is enabled:
   ```bash
   sudo raspi-config nonint get_camera  # Returns 0 if enabled
   ```
3. Test with:
   ```bash
   libcamera-hello --timeout 5000
   ```
4. Check `/boot/config.txt` includes `start_x=1` and `gpu_mem=128`

### Servo jitter

1. Use a dedicated 5V power supply for servos — USB power is insufficient
2. Add a capacitor (470uF-1000uF) across the servo power rails
3. Ensure solid ground connection between Pi and PCA9685
4. Reduce PWM frequency if needed (default is 50Hz, some servos prefer 60Hz)
5. Check that servo signal wires are short and away from motor power wires

### Service won't start

1. Check logs:
   ```bash
   sudo journalctl -u foldit -n 50
   ```
2. Verify the virtualenv exists:
   ```bash
   ls -la /opt/foldit/.venv/bin/python
   ```
3. Try running manually:
   ```bash
   cd /opt/foldit
   sudo -u pi .venv/bin/python -m foldit.main
   ```
4. Check file permissions:
   ```bash
   ls -la /opt/foldit/
   # Should be owned by pi:pi
   ```
