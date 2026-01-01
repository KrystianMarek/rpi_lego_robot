# Raspberry Pi Setup Guide

This guide covers setting up the K.O.C Robot server on a Raspberry Pi.

---

## Table of Contents

1. [OS Version Recommendations](#os-version-recommendations)
2. [Fixing Deprecated APT Sources (Stretch)](#fixing-deprecated-apt-sources-stretch)
3. [Quick Setup](#quick-setup)
4. [Manual Setup](#manual-setup)
5. [Hardware Verification](#hardware-verification)
6. [Troubleshooting](#troubleshooting)

---

## OS Version Recommendations

| OS Version | Debian Base | Status | Recommended |
|------------|-------------|--------|-------------|
| Stretch | Debian 9 | ❌ EOL (2022) | Not recommended |
| Buster | Debian 10 | ⚠️ Old stable | Acceptable |
| Bullseye | Debian 11 | ✅ Stable | **Recommended** |
| Bookworm | Debian 12 | ✅ Current | Best for new installs |

### Why Upgrade?

- **Security**: EOL releases don't receive security updates
- **Python**: Newer OS = newer Python (3.9+ for async features)
- **Packages**: Many packages no longer built for Stretch
- **Hardware**: Better RPi 4/5 support on newer releases

### How to Check Your Version

```bash
cat /etc/os-release
# Look for VERSION_CODENAME=stretch|buster|bullseye|bookworm
```

---

## Fixing Deprecated APT Sources (Stretch)

If you're stuck on Raspbian Stretch and see this error:

```
E: The repository 'http://raspbian.raspberrypi.org/raspbian stretch Release'
   does no longer have a Release file.
```

### Option 1: Use Archive Mirrors (Quick Fix)

```bash
# Backup current sources
sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup

# Replace with archive mirrors
sudo tee /etc/apt/sources.list << 'EOF'
# Debian Archive - Stretch (EOL)
deb http://archive.debian.org/debian stretch main contrib non-free
deb http://archive.debian.org/debian-security stretch/updates main contrib non-free

# Raspberry Pi archive (if available)
deb http://legacy.raspbian.org/raspbian/ stretch main contrib non-free rpi
EOF

# Disable signature checking for archived repos
sudo tee /etc/apt/apt.conf.d/99no-check-valid-until << 'EOF'
Acquire::Check-Valid-Until "false";
EOF

# Update package lists
sudo apt-get update
```

### Option 2: Upgrade to Bullseye (Recommended)

For a full OS upgrade, see the [official guide](https://www.raspberrypi.com/documentation/computers/os.html#upgrade-your-operating-system).

**Quick in-place upgrade** (backup your SD card first!):

```bash
# Update current system
sudo apt-get update && sudo apt-get upgrade -y

# Change stretch to bullseye
sudo sed -i 's/stretch/bullseye/g' /etc/apt/sources.list
sudo sed -i 's/stretch/bullseye/g' /etc/apt/sources.list.d/*.list

# Full upgrade
sudo apt-get update
sudo apt-get dist-upgrade -y

# Reboot
sudo reboot
```

---

## Quick Setup

For a fresh Raspberry Pi with internet access:

```bash
# Clone the repository
git clone https://github.com/your-repo/rpi_lego_robot.git
cd rpi_lego_robot

# Run the setup script
./scripts/setup-server.sh

# Activate the virtual environment
source .venv/bin/activate

# Start the server
python server.py
```

---

## Manual Setup

If the automated script fails, follow these steps:

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential cmake git pkg-config \
    libgtk2.0-dev libavcodec-dev libavformat-dev libswscale-dev \
    libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev \
    libtbb2 libtbb-dev \
    python3-dev python3-numpy \
    libusb-1.0-0-dev cython3 \
    libudev-dev
```

### 2. Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

### 3. Install Python via uv

uv can download and manage Python versions independently of the system:

```bash
# List available Python versions
uv python list

# Install Python 3.11 (recommended for RPi)
uv python install 3.11

# Or install latest (3.14) - may have compatibility issues with native libs
uv python install 3.14
```

### 4. Create Virtual Environment

```bash
uv venv .venv --python 3.11
source .venv/bin/activate
```

**Note:** We use Python 3.11 on RPi for compatibility with native libraries (libfreenect, BrickPi).
The client (desktop) uses Python 3.14 for latest features.

### 5. Install Python Dependencies

```bash
uv pip install -r requirements/server.txt
```

### 6. Initialize Submodules

```bash
git submodule init
git submodule update
```

### 7. Install BrickPi

```bash
# Fix serial port for RPi 3
sed -i 's/ttyAMA0/ttyS0/g' dependencies/BrickPi/Software/BrickPi_Python/BrickPi.py

# Install
uv pip install dependencies/BrickPi/Software/BrickPi_Python/
```

### 8. Install libfreenect (Kinect)

```bash
cd dependencies/libfreenect
mkdir -p build && cd build
cmake -D BUILD_PYTHON3=ON -D BUILD_CV=ON ..
make -j4
sudo make install
cd ../../..
```

### 9. Install NCS SDK (Optional - Legacy Device)

Only if you have an Intel Movidius Neural Compute Stick:

```bash
cd dependencies/ncsdk
./install.sh
cd ../..
```

### 10. Install udev Rules

```bash
sudo cp dependencies/66-kinect.rules /etc/udev/rules.d/
sudo cp dependencies/55-i2c.rules /etc/udev/rules.d/
sudo cp dependencies/ncsdk/api/src/97-usbboot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Hardware Verification

### Check Connected USB Devices

```bash
lsusb
```

Expected devices:
| Vendor:Product | Device |
|----------------|--------|
| `03e7:2150` | Intel Movidius NCS |
| `045e:02ae` | Xbox Kinect (audio) |
| `045e:02ad` | Xbox Kinect (camera) |
| `045e:02b0` | Xbox Kinect (motor) |

### Test Python Imports

```bash
source .venv/bin/activate

# Test Kinect
python -c "import freenect; print('Kinect: OK')"

# Test BrickPi
python -c "import BrickPi; print('BrickPi: OK')"

# Test NCS (if installed)
python -c "from mvnc import mvncapi; devices = mvncapi.EnumerateDevices(); print(f'NCS devices: {devices}')"
```

### Test I2C (Sensors)

```bash
# Enable I2C if not already
sudo raspi-config  # Interface Options -> I2C -> Enable

# List I2C devices
i2cdetect -y 1
```

---

## Troubleshooting

### "Permission denied" for USB devices

```bash
# Add user to required groups
sudo usermod -aG plugdev,i2c,video $USER

# Logout and login again
```

### Kinect not detected

```bash
# Check USB connection
lsusb | grep Xbox

# Check power - Kinect needs external power supply
# The RPi USB ports cannot power the Kinect

# Check kernel modules
lsmod | grep videodev
```

### NCS "MVCMD_NOT_FOUND" error

The NCS firmware wasn't downloaded correctly:

```bash
cd dependencies/ncsdk/api/src
./get_mvcmd.sh  # Re-download firmware
```

### BrickPi communication errors

```bash
# Check serial port
ls -la /dev/ttyS0

# Ensure I2C and serial are enabled
sudo raspi-config
# -> Interface Options -> Serial Port
# -> Interface Options -> I2C
```

### Out of memory during OpenCV build

```bash
# Increase swap
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=100/CONF_SWAPSIZE=2048/g' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Build with single thread
make -j1
```

---

## Network Configuration

### Static IP (Recommended for robot)

Edit `/etc/dhcpcd.conf`:

```bash
interface wlan0
static ip_address=192.168.10.187/24
static routers=192.168.10.1
static domain_name_servers=8.8.8.8
```

### Check IP Address

```bash
hostname -I
```

---

## Starting the Server

### Manual Start

```bash
cd ~/rpi_lego_robot
source .venv/bin/activate
python server.py
```

### Auto-start on Boot (systemd)

```bash
sudo tee /etc/systemd/system/koc-robot.service << EOF
[Unit]
Description=K.O.C Robot Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/rpi_lego_robot
Environment=PATH=$HOME/rpi_lego_robot/.venv/bin:/usr/bin
ExecStart=$HOME/rpi_lego_robot/.venv/bin/python server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable koc-robot
sudo systemctl start koc-robot

# Check status
sudo systemctl status koc-robot
```

---

## References

- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [libfreenect GitHub](https://github.com/OpenKinect/libfreenect)
- [BrickPi GitHub](https://github.com/DexterInd/BrickPi)
- [Intel NCS SDK (archived)](https://github.com/movidius/ncsdk)
- [uv Documentation](https://github.com/astral-sh/uv)

