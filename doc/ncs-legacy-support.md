# Intel Movidius Neural Compute Stick - Legacy Support

**Device Status:** Legacy / End-of-Life (as of 2025)
**SDK Version:** NCSDK 1.12.01.01 (final release)

---

## Overview

The Intel Movidius Neural Compute Stick (NCS) is a USB-based neural network accelerator. While Intel has discontinued the product line, the hardware remains functional for inference tasks.

### Device Identification

```bash
$ lsusb
Bus 001 Device 018: ID 03e7:2150  # Movidius NCS
```

| USB ID | State | Description |
|--------|-------|-------------|
| `03e7:2150` | Boot mode | Device ready for firmware upload |
| `03e7:f63b` | Running | Firmware loaded, ready for inference |

---

## Download URL Status

### Original Intel URL (DEAD ❌)

```
https://downloadmirror.intel.com/28192/eng/NCSDK-1.12.01.01.tar.gz
```

Returns 404 as Intel has removed the SDK from their servers.

### Working Mirror ✅

```
https://downloads.bl4ckb0x.de/downloadcenter.intel.com/28192/eng/NCSDK-1.12.01.01.tar.gz
```

This mirror has been verified working as of December 2025.

### Files Updated

The following files in this repository have been patched to use the working mirror:

- `dependencies/ncsdk/install.sh`
- `dependencies/ncsdk/api/src/get_mvcmd.sh`

---

## Installation

### Prerequisites

```bash
# System dependencies
sudo apt-get install -y libusb-1.0-0-dev libudev-dev

# udev rules for USB access
sudo cp dependencies/ncsdk/api/src/97-usbboot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add user to plugdev group
sudo usermod -aG plugdev $USER
# Logout/login required
```

### Full SDK Installation

```bash
cd dependencies/ncsdk
./install.sh
```

This installs:
- `libmvnc.so` - C/C++ API library
- `mvncapi.py` - Python API
- Firmware files in `/opt/movidius/`
- NCSDK toolkit (optional, for model compilation)

### Minimal Installation (API Only)

If you only need to run pre-compiled models:

```bash
cd dependencies/ncsdk/api/src

# Download firmware
./get_mvcmd.sh

# Build library
make -f Makefile.rpi

# Install
sudo make install
```

---

## Python API Usage

### Basic Device Enumeration

```python
from mvnc import mvncapi

# Find devices
devices = mvncapi.EnumerateDevices()
print(f"Found {len(devices)} NCS device(s): {devices}")

if not devices:
    print("No NCS device found!")
    exit(1)
```

### Load and Run a Model

```python
from mvnc import mvncapi
import numpy as np

# Open device
device = mvncapi.Device(devices[0])
device.OpenDevice()

# Load compiled graph (.graph file)
with open('model.graph', 'rb') as f:
    graph_data = f.read()

graph = device.AllocateGraph(graph_data)

# Prepare input (example: 224x224 RGB image)
input_data = np.zeros((224, 224, 3), dtype=np.float16)

# Run inference
graph.LoadTensor(input_data.astype(np.float16), None)
output, _ = graph.GetResult()

print(f"Output shape: {output.shape}")

# Cleanup
graph.DeallocateGraph()
device.CloseDevice()
```

### Status Codes

```python
from mvnc.mvncapi import Status

# Common status codes
Status.OK              # Success
Status.BUSY            # Device busy
Status.DEVICE_NOT_FOUND
Status.MVCMD_NOT_FOUND # Firmware not found
Status.TIMEOUT
```

---

## Model Compilation

**Note:** The NCSDK toolkit requires additional dependencies (Caffe/TensorFlow) and is complex to set up on modern systems.

### Pre-compiled Models

The `ncappzoo` submodule contains pre-compiled models:

```bash
cd dependencies/ncappzoo/networks
ls */  # Available networks
```

### Compiling Your Own Models

If you have the toolkit installed:

```bash
# From Caffe
mvNCCompile model.prototxt -w model.caffemodel -o model.graph

# From TensorFlow (frozen graph)
mvNCCompile model.pb -in input_node -on output_node -o model.graph
```

---

## Troubleshooting

### "MVCMD_NOT_FOUND" Error

The firmware wasn't downloaded or is corrupted:

```bash
cd dependencies/ncsdk/api/src
rm -rf mvnc/  # Remove old firmware
./get_mvcmd.sh  # Re-download
```

### "DEVICE_NOT_FOUND" Error

1. Check USB connection:
   ```bash
   lsusb | grep 03e7
   ```

2. Check udev rules:
   ```bash
   ls -la /etc/udev/rules.d/ | grep usbboot
   ```

3. Check permissions:
   ```bash
   groups  # Should include 'plugdev'
   ```

4. Try unplugging and replugging the device

### "TIMEOUT" Error

The device may be in a bad state:

```bash
# Reset by power cycling
# Unplug USB, wait 5 seconds, replug

# Check dmesg for USB errors
dmesg | tail -20
```

### Library Not Found

```bash
# Check library installation
ldconfig -p | grep mvnc

# If missing, add to library path
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Or reinstall
cd dependencies/ncsdk/api/src
sudo make install
sudo ldconfig
```

---

## Alternative: OpenVINO

For newer Intel hardware (NCS2, Neural Compute Stick 2), use OpenVINO instead:

- [OpenVINO Toolkit](https://docs.openvino.ai/)
- NCS2 uses different USB ID: `03e7:2485`

**Note:** NCS1 (this device) is NOT supported by OpenVINO.

---

## Hardware Specifications

| Specification | Value |
|--------------|-------|
| Processor | Intel Movidius Myriad 2 VPU |
| Performance | ~100 GFLOPS (FP16) |
| Power | ~1W typical |
| Interface | USB 3.0 (works on USB 2.0) |
| Supported Frameworks | Caffe, TensorFlow (via NCSDK) |
| Precision | FP16 |

---

## References

- [NCSDK GitHub (archived)](https://github.com/movidius/ncsdk)
- [ncappzoo - Model Zoo](https://github.com/movidius/ncappzoo)
- [Intel NCS Documentation (archived)](https://movidius.github.io/ncsdk/)

