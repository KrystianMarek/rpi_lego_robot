# Future Improvements TODO

Last updated: December 2025

## Completed ✅

### Bug Fixes
- [x] **Depth image display bug** — Was using `video_frame.data` instead of `depth_array.data`, causing depth to show corrupted video
- [x] **Signal typo** — Fixed `kinect_packet_singal` → `kinect_packet_signal`
- [x] **ENV support for robot IP** — Added `ROBOT_IP` environment variable support in `gui.py`
- [x] **Depth normalization** — Kinect depth is 11-bit, now properly converted to 8-bit for display

### Code Quality
- [x] **requirements.txt** — Created at project root
- [x] **Moved numpy import** — From inline to top of MainWindowWrapper.py

### Bug Fixes (Session 2)
- [x] **Keyboard focus bug** — After connect, IP field now disabled to prevent shortcut hijacking
- [x] **ROBOT_IP env var** — Fixed environment variable loading
- [x] **UI Typo** — Fixed `turrent` → `turret` in all UI and code files

### Architecture
- [x] **Central Config** — Created `app/common/config.py` with all ports, timeouts, and Kinect calibration
- [x] **FrameProcessor** — Created `app/client/frame_processor.py` with video/depth/pointcloud conversion
- [x] **ConnectionManager** — Created `app/client/connection_manager.py` with state machine, connect/disconnect support

### Known Issues (Suppressed)
- [x] **Numpy version warning** — Server (RPi) has older numpy; client shows `VisibleDeprecationWarning` on pickle. Suppressed in `gui.py`.

### Features Added
- [x] **System Stats Display** — CPU, RAM, WiFi bandwidth from robot shown in status bar
- [x] **FPS Counter** — Video and depth FPS shown in status bar (updated every 1s)
- [x] **ZMQ Timeout Handling** — Poller with 500ms timeout, connection timeout detection
- [x] **Point Cloud Widget** — 3D visualization using pyqtgraph GLViewWidget with view controls
- [x] **Video Mode Radio Buttons** — Video/Depth/Cloud Point modes now functional
- [x] **Auto Disconnect** — Clean disconnect on window close or Ctrl+C

---

## ⚠️ Prerequisites: Architecture Improvements

**Before implementing features below, complete the architectural refactoring.**

See: [`architecture-improvements.md`](architecture-improvements.md)

| Priority | Change | Effort | Enables |
|----------|--------|--------|---------|
| ~~1~~ | ~~Central Config~~ | ~~1-2 hrs~~ | ✅ Done |
| ~~2~~ | ~~FrameProcessor~~ | ~~2-3 hrs~~ | ✅ Done |
| ~~3~~ | ~~ConnectionManager~~ | ~~3-4 hrs~~ | ✅ Done |

**✅ Architecture improvements complete!**

Features now ready:
- Point Cloud & depth colormaps (via FrameProcessor)
- Connect/Disconnect button (via ConnectionManager)
- Connection status indicator (via ConnectionManager state)

---

## Pending 🔲

---

### Medium Priority

#### Point Cloud Support
**Current state:** GUI has "Cloud Point" radio button but no implementation.

**libfreenect capabilities:**
- `freenect.sync_get_depth()` returns raw depth values
- Depth can be converted to real-world XYZ coordinates using Kinect calibration parameters
- Formula: `Z = depth_value`, `X = (x - cx) * Z / fx`, `Y = (y - cy) * Z / fy`

**Implementation options:**
1. **Simple approach**: Use depth + RGB to create colored point cloud on client
2. **Server-side**: Generate point cloud on Pi (CPU intensive)
3. **Visualization**: Use PyQtGraph, Open3D, or vispy for 3D rendering

**Files to modify:**
- `app/Networking/KinectPacket.py` — Add point cloud data field (optional)
- `app/client/gui/MainWindowWrapper.py` — Add point cloud visualization widget
- `app/client/gui/main_window.ui` — Add 3D viewer widget area

**Kinect intrinsic parameters (approximate):**
```python
fx = 594.21  # focal length x
fy = 591.04  # focal length y
cx = 339.5   # principal point x
cy = 242.7   # principal point y
```

---

#### Depth-RGB Alignment
**Issue:** Depth and RGB cameras on Kinect are physically offset (~2.5cm apart), causing misalignment.

**Current state:** Depth and video frames are captured independently, not registered.

**Solutions:**
1. **Software registration**: Use Kinect calibration to project depth onto RGB plane
2. **libfreenect option**: Check if `freenect.sync_get_video()` with `FREENECT_VIDEO_IR_8BIT` provides aligned data
3. **OpenCV approach**: Use `cv2.registerDepth()` if available

**Reference:** libfreenect has `freenect_camera_to_world()` function for coordinate conversion.

---

### Low Priority

#### Code Quality
- [ ] Add `requirements.txt` at project root
- [ ] Remove unused `app/common/ControlPacket.py`
- [ ] Add type hints throughout codebase
- [ ] Add unit tests for packet serialization
- [ ] Consider replacing pickle with msgpack or protobuf for safety

#### GUI Improvements
- [x] Add disconnect button — Connect button now toggles to "Disconnect" when connected
- [ ] Show connection status indicator (green/red) — State available via ConnectionManager
- [x] ~~Add keyboard shortcuts for movement (WASD)~~ — Already implemented!
- [ ] Add keyboard shortcut hints to UI buttons (tooltips or labels)
- [ ] Remember last robot IP in config file
- [x] Add FPS counter for video stream — Shows in status bar
- [x] Add depth colormap options (jet, viridis, etc.) — Jet colormap in Depth/Cloud modes

**Existing keyboard shortcuts:**
| Key | Action |
|-----|--------|
| W | Forward |
| S | Backward |
| A | Turn Left (pivot) |
| D | Turn Right (pivot) |
| Q | Curve Left |
| E | Curve Right |
| [ | Turret Left |
| ] | Turret Right |

#### Server Improvements
- [ ] Add graceful shutdown handling
- [ ] Add configurable frame rate limiting
- [x] Add CPU/memory monitoring to telemetry — Done! System stats in status bar

#### Kinect Tilt Motor Control
**Status:** Not implemented (returns 0 in `KinectProcess.py`)

**libfreenect supports tilt control:**
```python
freenect.set_tilt_degs(dev, angle)  # Set tilt (-30° to +30°)
freenect.get_tilt_degs(state)       # Get current angle
freenect.get_tilt_state(dev)        # Get state object
freenect.get_tilt_status(state)     # Motor status (moving/stopped)
```

**Implementation needed:**
1. Add `set_tilt_degs()` method to `KinectProcess`
2. Create `KinectTiltCommand` packet type
3. Wire command from GUI to server via CommandReceiver
4. Add tilt slider/buttons to GUI (range: -30° to +30°)

**Files to modify:**
- `app/server/KinectProcess.py` — Uncomment and implement tilt methods
- `app/Networking/CommandPacket.py` — Add `KinectTilt` command
- `app/server/CommandReceiver.py` — Handle tilt command
- `app/client/gui/main_window.ui` — Add tilt slider widget

#### Networking
- [ ] Add connection timeout handling
- [ ] Implement reconnection logic
- [ ] Add network quality indicator (latency, packet loss)
- [ ] Consider WebSocket alternative for browser-based client

---

## Research Notes

### libfreenect Point Cloud
From libfreenect documentation:
- Raw depth is in "disparity" units, not millimeters
- Conversion formula: `depth_meters = 0.1236 * tan(raw_depth / 2842.5 + 1.1863)`
- Alternative: Use registered depth mode if available

### Depth Data Format
- Kinect returns 11-bit depth (0-2047)
- Value 2047 = no reading / too far / too close
- Typical range: 0.5m to 4m
- Raw values are NOT linear distance

### Performance Considerations
- Point cloud generation is CPU intensive
- Consider generating on-demand rather than every frame
- Subsample depth for faster processing (e.g., every 4th pixel)

---

## Environment Setup

### Required for point cloud visualization:
```bash
pip install pyqtgraph  # Fast 2D/3D plotting with Qt
# or
pip install open3d     # Full point cloud library
# or
pip install vispy      # GPU-accelerated visualization
```

### Optional for better ENV handling:
```bash
pip install python-dotenv
```

Then create `.env` file:
```
ROBOT_IP=192.168.10.187
```

---

## Hardware-Dependent Features (Future)

These features require physical modifications or additional hardware setup.

### Turret Auto-Reset / Home Position
**Requires:** Physical color marker + color sensor integration

**Description:** Automatically return turret to home position using color sensor feedback.

**Implementation approach:**
1. Mount a colored marker (e.g., red tape) at turret's home position
2. Color sensor detects marker when turret passes over it
3. Server-side logic: rotate turret slowly until color sensor reads marker
4. Stop when home position detected

**Files to modify:**
- `app/server/CommandReceiver.py` — Add `TurretReset` handling with color sensor feedback
- `app/server/BrickPiWrapper.py` — Add color sensor threshold detection
- `app/Networking/CommandPacket.py` — May need new packet type for async reset status

**Notes:**
- Current `TurretReset` command just sets speed to 0
- Need closed-loop control for true homing
- Consider adding encoder-based fallback (rotate N degrees if no marker found)

