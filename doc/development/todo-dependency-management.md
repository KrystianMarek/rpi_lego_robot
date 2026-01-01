# TODO: Dependency Management Refactoring

**Created:** December 2025
**Status:** Planning
**Priority:** High (blocks further robot development)

---

## Overview

This document outlines the refactoring of dependency management for the K.O.C Robot project. The goal is to:

1. Fix broken Intel NCS SDK download URL (legacy device support)
2. Update Raspbian sources (Stretch → Buster/Bullseye)
3. Implement proper Python virtual environment management using `uv`
4. Split requirements into server (Raspberry Pi) and client (PC) configurations

---

## Problem Analysis

### 1. Intel Movidius NCS SDK - Broken Download URL

**Device Status:** Legacy (end of 2025), but still functional hardware.

**Issue:** Original Intel download URL is dead:
```
# DEAD URL (404)
https://downloadmirror.intel.com/28192/eng/NCSDK-1.12.01.01.tar.gz
```

**Working Mirror:**
```
https://downloads.bl4ckb0x.de/downloadcenter.intel.com/28192/eng/NCSDK-1.12.01.01.tar.gz
```

**Affected Files:**
- `dependencies/ncsdk/install.sh` (line 9)
- `dependencies/ncsdk/api/src/get_mvcmd.sh` (line 9)

**Device Recognition Confirmed:**
```bash
$ lsusb
Bus 001 Device 018: ID 03e7:2150  # Movidius NCS
```

**NCS SDK Dependencies:**
| Component | Type | Notes |
|-----------|------|-------|
| `libusb-1.0-dev` | System | USB communication |
| `libudev-dev` | System | Device detection |
| `libmvnc.so` | Built | From ncsdk source |
| `numpy` | Python | Required by `mvncapi.py` |
| `97-usbboot.rules` | udev | USB permissions |

---

### 2. Raspbian Sources - Deprecated Stretch Release

**Current Error:**
```
$ sudo apt update
Err:3 http://raspbian.raspberrypi.org/raspbian stretch Release
  404  Not Found [IP: 93.93.128.193 80]
E: The repository '...stretch Release' does no longer have a Release file.
```

**Root Cause:** Raspbian Stretch (based on Debian 9) reached end-of-life.

**Available Options:**

| OS Version | Debian Base | Status | Python |
|------------|-------------|--------|--------|
| Stretch | Debian 9 | ❌ EOL | 3.5 |
| Buster | Debian 10 | ⚠️ LTS until 2024 | 3.7 |
| Bullseye | Debian 11 | ✅ Supported | 3.9 |
| Bookworm | Debian 12 | ✅ Current | 3.11 |

**Recommended Actions:**
1. **Short-term:** Update APT sources to use archive mirrors
2. **Long-term:** Consider OS upgrade to Bullseye/Bookworm

**Archive Sources (for Stretch):**
```bash
# /etc/apt/sources.list
deb http://archive.debian.org/debian stretch main
```

---

### 3. Missing venv Support in `install_dependencies.sh`

**Current Issues:**
- Direct `pip install` pollutes system Python
- No isolation between projects
- Version conflicts risk
- Breaks on newer Raspbian with externally-managed Python

**Proposed Tool:** `uv` - Ultra-fast Python package manager

```bash
$ uv -h
An extremely fast Python package manager.

Usage: uv [OPTIONS] <COMMAND>
```

**uv Benefits:**
- 10-100x faster than pip
- Built-in venv management
- Lock file support
- **Python version management** - install any Python version without system packages:
  ```bash
  uv python install 3.14    # Download Python 3.14
  uv python list            # Show available versions
  uv venv --python 3.14     # Create venv with specific version
  ```
- Works on ARM (Raspberry Pi) and x86

---

### 4. No Client/Server Separation in Requirements

**Current `requirements.txt`** mixes both:
```
# Client only
PyQt5>=5.15.0
pyqtgraph>=0.12.0
PyOpenGL>=3.1.0

# Server only
psutil>=5.8.0
# smbus2 - I2C (comment only)
```

**Proposed Structure:**
```
requirements/
├── base.txt        # Shared: numpy, pyzmq, PyYAML, netifaces
├── client.txt      # GUI: PyQt5, pyqtgraph, PyOpenGL, opencv-python
└── server.txt      # RPi: smbus2, psutil, BrickPi, freenect
```

---

## Proposed Solution

### New File Structure

```
rpi_lego_robot/
├── requirements/
│   ├── base.txt        # Core dependencies (both platforms)
│   ├── client.txt      # Desktop GUI dependencies
│   └── server.txt      # Raspberry Pi dependencies
├── scripts/
│   ├── setup-client.sh # Client setup (Linux/macOS)
│   ├── setup-server.sh # Server setup (Raspberry Pi)
│   └── common.sh       # Shared functions
├── .python-version     # Pin Python version (uv)
├── pyproject.toml      # Modern Python project config (optional)
└── install_dependencies.sh  # DEPRECATED (keep for reference)
```

---

## Implementation Tasks

### Phase 1: Fix Critical Issues

- [ ] **1.1 Update NCS SDK download URL**
  - Modify `dependencies/ncsdk/install.sh`
  - Modify `dependencies/ncsdk/api/src/get_mvcmd.sh`
  - Mirror URL: `https://downloads.bl4ckb0x.de/downloadcenter.intel.com/28192/eng/NCSDK-1.12.01.01.tar.gz`

- [ ] **1.2 Document Raspbian archive sources**
  - Create `doc/raspberry-pi-setup.md`
  - Include APT source fixes for Stretch
  - Include OS upgrade path recommendations

- [ ] **1.3 Copy NCS udev rules**
  - Add to `dependencies/97-usbboot.rules`
  - Include in install script

### Phase 2: Requirements Restructure

- [ ] **2.1 Create `requirements/` directory**

- [ ] **2.2 Create `requirements/base.txt`**
  ```
  numpy>=1.19.0
  pyzmq>=22.0.0
  PyYAML>=5.0
  netifaces>=0.10.0
  python-dotenv>=0.19.0
  ```

- [ ] **2.3 Create `requirements/client.txt`**
  ```
  -r base.txt
  PyQt5>=5.15.0
  pyqtgraph>=0.12.0
  PyOpenGL>=3.1.0
  opencv-python>=4.0.0
  ```

- [ ] **2.4 Create `requirements/server.txt`**
  ```
  -r base.txt
  smbus2>=0.4.0
  psutil>=5.8.0
  # Native builds (handled by setup script):
  # - BrickPi (from submodule)
  # - freenect (from submodule)
  # - mvnc (from ncsdk)
  ```

### Phase 3: uv Integration

- [x] **3.1 Create `.python-version`**
  ```
  3.14
  ```

  **Python Version Strategy:**
  | Platform | Version | Rationale |
  |----------|---------|-----------|
  | Client (PC) | 3.14 | Latest features, uv downloads automatically |
  | Server (RPi) | 3.11 | Native lib compatibility (libfreenect, BrickPi) |

  uv can install any Python version independently of the system:
  ```bash
  uv python install 3.14
  uv venv .venv --python 3.14
  ```

- [ ] **3.2 Create `scripts/common.sh`**
  - Functions for:
    - `install_uv()` - Install uv if missing
    - `setup_venv()` - Create/activate venv
    - `detect_platform()` - RPi vs x86
    - `check_submodules()` - Init git submodules

- [ ] **3.3 Create `scripts/setup-client.sh`**
  ```bash
  #!/usr/bin/env bash
  set -e
  source scripts/common.sh

  install_uv
  uv venv .venv
  source .venv/bin/activate
  uv pip install -r requirements/client.txt

  echo "Client setup complete. Activate with: source .venv/bin/activate"
  ```

- [ ] **3.4 Create `scripts/setup-server.sh`**
  ```bash
  #!/usr/bin/env bash
  set -e
  source scripts/common.sh

  # Update package lists (with archive fallback)
  update_apt_sources
  install_system_deps

  install_uv
  uv venv .venv
  source .venv/bin/activate
  uv pip install -r requirements/server.txt

  # Build native dependencies
  install_libfreenect
  install_brickpi
  install_ncsdk  # With fixed URL

  # Copy udev rules
  copy_udev_rules

  echo "Server setup complete. Activate with: source .venv/bin/activate"
  ```

### Phase 4: NCS SDK Integration

- [ ] **4.1 Create `scripts/install-ncsdk.sh`**
  - Standalone NCS SDK installer
  - Uses mirror URL
  - Handles firmware extraction
  - Builds `libmvnc.so` from source
  - Copies Python bindings to venv

- [ ] **4.2 Add NCS udev rules setup**
  - Copy `dependencies/ncsdk/api/src/97-usbboot.rules`
  - Reload udev: `udevadm control --reload-rules`

- [ ] **4.3 Test NCS device access**
  ```python
  # testing/ncs/test_device.py
  from mvnc import mvncapi
  devices = mvncapi.EnumerateDevices()
  print(f"Found {len(devices)} NCS devices: {devices}")
  ```

### Phase 5: Documentation

- [ ] **5.1 Update README.md**
  - New setup instructions using uv
  - Client vs server setup commands

- [ ] **5.2 Create `doc/raspberry-pi-setup.md`**
  - OS version recommendations
  - APT source fixes
  - uv installation on ARM

- [ ] **5.3 Create `doc/ncs-legacy-support.md`**
  - Device recognition troubleshooting
  - Mirror URL documentation
  - Example usage code

---

## Current `install_dependencies.sh` Analysis

### Functions to Preserve

| Function | Keep | Notes |
|----------|------|-------|
| `install_system_dependencies()` | ✅ | Adapt for scripts/setup-server.sh |
| `install_opencv()` | ⚠️ | Consider using pre-built wheels instead |
| `install_brickpi()` | ✅ | Keep sed hack for RPi3 |
| `install_libfreenect()` | ✅ | Keep cmake build |

### Issues in Current Script

```bash
# Line 87 - Installs to system Python (bad)
pip install numpy smbus2 pyzmq pyaml netifaces

# Line 62 - Assumes pip install from submodule works
pip install dependencies/BrickPi/Software/BrickPi_Python/

# Line 48 - Symlinks to unknown site-packages
ln -s /usr/local/lib/python$(python_version)/site-packages/cv2*.so ${site_packages_dir}/cv2.so
```

### Duplicate Dependencies

| Package | Current script | requirements.txt | Action |
|---------|---------------|------------------|--------|
| numpy | pip install | ✅ | Remove from script |
| pyzmq | pip install | ✅ | Remove from script |
| PyYAML | pip install (as pyaml) | ✅ | Remove from script |
| netifaces | pip install | ✅ | Remove from script |
| smbus2 | pip install | ❌ (comment) | Add to server.txt |

---

## Environment Variables

The new setup should support:

```bash
# .env file (gitignored)
ROBOT_IP=192.168.10.187
NCSDK_MIRROR_URL=https://downloads.bl4ckb0x.de/...
```

---

## Testing Checklist

### Client Setup (PC/Mac)
- [ ] `uv` installs successfully
- [ ] `.venv` created with correct Python version
- [ ] `gui.py` starts without import errors
- [ ] PyQt5 GUI renders correctly
- [ ] Can connect to robot (if available)

### Server Setup (Raspberry Pi)
- [ ] APT sources updated/fixed
- [ ] System dependencies install
- [ ] `uv` installs on ARM
- [ ] `.venv` created
- [ ] BrickPi imports work
- [ ] freenect imports work
- [ ] NCS device detected
- [ ] `server.py` starts without errors

### NCS Specific
- [ ] `lsusb` shows device `03e7:2150`
- [ ] udev rules applied (no sudo needed)
- [ ] `mvncapi.EnumerateDevices()` returns device
- [ ] Can load/run model (optional)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| NCS mirror goes down | High | Mirror locally, document alternatives |
| uv breaks on old ARM | Medium | Fallback to pip+venv |
| OS upgrade breaks BrickPi | High | Test on spare SD card first |
| libfreenect fails to build | Medium | Document known-good commit |

---

## References

- [uv Documentation](https://github.com/astral-sh/uv)
- [Intel NCS SDK Archive](https://github.com/movidius/ncsdk)
- [Raspberry Pi OS Versions](https://www.raspberrypi.com/software/operating-systems/)
- [Debian Archive](http://archive.debian.org/debian/)
- [libfreenect](https://github.com/OpenKinect/libfreenect)

---

## Next Steps

1. Start with **Phase 1** - fix critical blockers
2. Test NCS device with fixed URL
3. Implement uv-based setup scripts
4. Validate on actual Raspberry Pi hardware
5. Update main README with new instructions

