# K.O.C - Kinect on Caterpillar

A remote-controlled LEGO robot featuring caterpillar tracks, a rotating turret, and Xbox 360 Kinect vision — powered by Raspberry Pi 3 and BrickPi+.

![pic1](pictures/pic1.jpg "Robot Front View")
![pic2](pictures/pic2.jpg "Robot Side View")

[![YouTube Demo](https://img.youtube.com/vi/l-SW-rKROMY/0.jpg)](https://www.youtube.com/watch?v=l-SW-rKROMY)

## Features

- **Caterpillar drive** with differential steering (pivot turns, curves)
- **Rotating turret** with mounted Kinect sensor
- **Real-time video streaming** (RGB + depth) from Kinect
- **Telemetry display**: motor encoders, sensors, battery voltage, CPU temperature
- **PyQt5 GUI** for remote control from any PC
- **ZeroMQ networking** for low-latency communication

## Hardware

| Component | Model |
|-----------|-------|
| Computer | [Raspberry Pi 3](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/) |
| Motor Interface | [BrickPi+](https://www.dexterindustries.com/brickpi/) |
| Camera | [Xbox 360 Kinect](https://en.wikipedia.org/wiki/Kinect) |
| Motors & Sensors | [LEGO 8547 Mindstorms NXT 2.0](https://www.bricklink.com/v2/catalog/catalogitem.page?S=8547-1) |
| Chassis | [LEGO 42055 Bucket Wheel Excavator](https://www.bricklink.com/v2/catalog/catalogitem.page?S=42055-1) (tracks) |

See [Hardware Documentation](doc/hardware.md) for wiring details.

## Quick Start

### Server (Raspberry Pi)

1. Configure Raspberry Pi (add to `/boot/config.txt`):
   ```bash
   dtoverlay=brickpi
   init_uart_clock=32000000
   dtparam=brickpi_battery=okay
   ```

2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ./install_dependencies.sh $(.venv/bin/python -c "import site; print(site.getsitepackages()[0])")
   ```

3. Run the server:
   ```bash
   source .venv/bin/activate
   python server.py
   ```

### Client (PC)

1. Install client dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install numpy pyzmq pyyaml netifaces opencv-python pyqt5
   ```

2. Run the GUI:
   ```bash
   source .venv/bin/activate
   python gui.py
   ```

3. Enter the robot's IP address and click **Connect**

## Architecture

```
┌──────────────────────┐              ┌──────────────────────┐
│  CLIENT (PC)         │   TCP/IP    │  SERVER (RPi)        │
│                      │◄───────────►│                      │
│  PyQt5 GUI           │   ZeroMQ    │  BrickPi + Kinect    │
│  - Movement controls │             │  - Motor control     │
│  - Telemetry display │             │  - Sensor reading    │
│  - Video streaming   │             │  - Camera capture    │
└──────────────────────┘              └──────────────────────┘
```

See [Architecture Documentation](doc/architecture.md) for detailed design.

## Controls

| Control | Action |
|---------|--------|
| ↑ Forward | Both tracks forward |
| ↓ Backward | Both tracks reverse |
| ← Turn Left | Pivot turn (tracks opposite) |
| → Turn Right | Pivot turn (tracks opposite) |
| ↖ Curve Left | Differential steering |
| ↗ Curve Right | Differential steering |
| Turret Left/Right | Rotate camera mount |
| Speed Slider | Adjust motor power (0-255) |

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](doc/architecture.md) | System design and data flow |
| [Hardware](doc/hardware.md) | Wiring, sensors, and configuration |
| [Networking](doc/networking.md) | Protocol and packet formats |
| [Project Structure](doc/development/project-structure.md) | Code organization |

## UI Development

The GUI is built with Qt Designer. To regenerate after editing:

```bash
pyuic5 app/client/gui/main_window.ui -o app/client/gui/main_window.py
```

## Dependencies

### Python Packages
- `numpy` - Array operations
- `pyzmq` - ZeroMQ messaging
- `pyyaml` - Configuration
- `netifaces` - Network discovery
- `opencv-python` - Image processing
- `pyqt5` - GUI framework
- `smbus2` - I²C (server only)

### Native Libraries
- **BrickPi** - LEGO motor/sensor interface (git submodule)
- **libfreenect** - Kinect driver (git submodule)

Initialize submodules:
```bash
git submodule init
git submodule update
```

## Resources

### Documentation
- [PyQt5 Tutorial](http://zetcode.com/gui/pyqt5/)
- [ZeroMQ Guide](http://zguide.zeromq.org/py:all)
- [PyZMQ Docs](https://pyzmq.readthedocs.io)
- [BrickPi Documentation](https://www.dexterindustries.com/BrickPi/brickpi-tutorials-documentation/)
- [OpenKinect](https://openkinect.org/)

## License

See [LICENSE](LICENSE) file.
