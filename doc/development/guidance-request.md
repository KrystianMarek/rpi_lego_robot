# K.O.C Robot Project - Technical Guidance Request

## Project Overview

**K.O.C Robot** is a remote-controlled LEGO robot built on a Raspberry Pi 3 with:
- **BrickPi+** motor controller (LEGO Mindstorms motors/sensors)
- **Xbox 360 Kinect** sensor (RGB video + 11-bit depth)
- **PyQt5 GUI client** running on a Mac/PC

The robot streams video, depth, and telemetry to a desktop client over WiFi. The client sends movement commands back to the robot.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (Mac/PC)                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  gui.py → MainWindowWrapper                              │    │
│  │    ├── ConnectionManager (state machine)                 │    │
│  │    ├── FrameProcessor (video/depth conversion)           │    │
│  │    ├── TelemetryClient (ZMQ SUB, receives data)          │    │
│  │    └── CommandClient (ZMQ PUSH, sends commands)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│              ZMQ PUSH ────┼──── ZMQ SUB                          │
│            (commands)     │   (telemetry)                        │
└───────────────────────────┼──────────────────────────────────────┘
                            │ WiFi
┌───────────────────────────┼──────────────────────────────────────┐
│                    SERVER (Raspberry Pi 3)                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  server.py                                               │    │
│  │    ├── HelloServer (ZMQ REQ/REP handshake)               │    │
│  │    ├── CommandReceiver (ZMQ PULL, receives commands)     │    │
│  │    ├── BrickPiWrapper (motor control, sensors, psutil)   │    │
│  │    ├── KinectProcess (freenect, video+depth capture)     │    │
│  │    └── TelemetryPublisher (ZMQ PUB, broadcasts data)     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Server OS | Raspbian (Python 3.5) |
| Client OS | macOS (Python 3.11) |
| GUI | PyQt5 |
| Networking | ZeroMQ (pyzmq) |
| Serialization | pickle + zlib compression |
| Kinect Driver | libfreenect (freenect Python bindings) |
| Motor Control | BrickPi Python library |
| System Stats | psutil |

## Current Data Flow

### Kinect Data (Server → Client)
```python
# Server: KinectProcess.py
video_frame = freenect.sync_get_video()[0]  # RGB 640x480x3
depth_array = freenect.sync_get_depth()[0]  # 11-bit 640x480

packet = KinectPacket(sequence)
packet.set_video_frame(video_frame)  # numpy array
packet.set_depth(depth_array)        # numpy array
sender.send(compress(packet))        # pickle + zlib
```

### Client Display
```python
# Client: MainWindowWrapper.py
def update_kinect(self, data: KinectPacket):
    video_image = FrameProcessor.video_to_qimage(data.get_video_frame())
    depth_image = FrameProcessor.depth_to_qimage(data.get_depth(), colormap='grayscale')
    self._main_window.kinect_video.setPixmap(QPixmap.fromImage(video_image))
    self._main_window.label_10.setPixmap(QPixmap.fromImage(depth_image))
```

### FrameProcessor (already implemented)
```python
# Client: app/client/frame_processor.py
class FrameProcessor:
    @staticmethod
    def video_to_qimage(video_frame: np.ndarray) -> QImage: ...

    @staticmethod
    def depth_to_qimage(depth_array: np.ndarray, colormap='grayscale') -> QImage: ...

    @staticmethod
    def depth_to_pointcloud(depth_array, fx=594.21, fy=591.04, cx=339.5, cy=242.7) -> np.ndarray:
        """Returns (N, 3) XYZ point cloud."""
        # Already implemented with Kinect intrinsics from Config

    @staticmethod
    def depth_to_colored_pointcloud(depth_array, video_frame, ...) -> tuple:
        """Returns (points, colors) for colored point cloud."""
        # Already implemented
```

---

## Questions Needing Guidance

### 1. Point Cloud Visualization in PyQt5

**Context:**
- I have `FrameProcessor.depth_to_pointcloud()` that converts depth to XYZ coordinates
- The GUI has a "Cloud Point" radio button that currently does nothing
- Point cloud is ~307,200 points per frame (640×480) at ~10 FPS

**Questions:**
1. What's the best PyQt5-compatible 3D visualization library for real-time point clouds?
   - `pyqtgraph.opengl.GLViewWidget`?
   - `vispy`?
   - `Open3D` with Qt integration?

2. How do I embed a 3D OpenGL widget into an existing PyQt5 QMainWindow alongside 2D QLabel widgets?

3. What's a reasonable point cloud density for smooth rendering? Should I subsample (every 4th pixel)?

4. Code example for rendering a colored point cloud in pyqtgraph's GLScatterPlotItem?

---

### 2. Depth-RGB Camera Alignment (Kinect v1)

**Context:**
- Kinect v1 has RGB and depth cameras physically offset by ~2.5cm
- Current depth and video frames are captured separately, not aligned
- Looking at the robot from depth camera's perspective doesn't match RGB camera's perspective

**Questions:**
1. Is there a simple libfreenect function to get registered/aligned depth?
   - I see references to `freenect.sync_get_depth(format=FREENECT_DEPTH_REGISTERED)` but unclear if this works

2. If manual alignment is needed, what's the transformation matrix between depth and RGB cameras?
   - Do I need camera calibration, or are there known default values for Kinect v1?

3. Is OpenCV's `cv2.rgbd.registerDepth()` compatible with libfreenect depth data?

4. For point cloud coloring, should alignment happen:
   - On the server (transform depth before sending)?
   - On the client (transform when building point cloud)?

---

### 3. ZMQ Reconnection Handling

**Context:**
- Client connects to robot via ZMQ PUSH/SUB sockets
- If robot restarts or WiFi drops, client currently hangs or crashes
- ConnectionManager has state machine but no timeout/reconnection logic

**Current socket setup:**
```python
# Client: TelemetryClient
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://{}:5559".format(robot_ip))
subscriber.setsockopt(zmq.SUBSCRIBE, b'')

# Blocking receive (problem!)
data = subscriber.recv()  # Hangs forever if robot offline
```

**Questions:**
1. What's the correct ZMQ pattern for detecting disconnection?
   - `RCVTIMEO` socket option?
   - Heartbeat messages?
   - `zmq.Poller` with timeout?

2. How should I structure reconnection logic?
   - Exponential backoff?
   - Should I destroy and recreate sockets, or can I reuse them?

3. Is there a way to detect "robot went offline" vs "temporary network hiccup"?

4. Code example for non-blocking ZMQ receive with timeout in a QThread?

---

## Constraints

- Server runs Python 3.5 (no f-strings, no `1_000_000` literals)
- Client runs Python 3.11 (modern syntax OK)
- Pickle protocol must be 4 (not 5) for cross-version compatibility
- GUI must remain responsive during streaming (~10 FPS)
- Raspberry Pi 3 has limited CPU (avoid heavy server-side processing)

---

# Guidance Received

## 1. Point Cloud Visualization in PyQt5

### Recommended Approach
**pyqtgraph** using `GLViewWidget` + `GLScatterPlotItem` is best for real-time point clouds:
- Lightweight, pure Python/Qt
- Handles hundreds of thousands of points with GPU acceleration
- Native Qt widget integration

### Point Cloud Density
- Full 307k points is too dense for smooth rendering
- **Subsample to ~50k–100k points** (stride=2 → ~77k points)
- Use numpy slicing: `depth[::2, ::2]`

### Code Example
```python
import pyqtgraph.opengl as gl
import numpy as np

class PointCloudWidget(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opts['distance'] = 2000  # Initial camera distance

        # Grid for reference
        grid = gl.GLGridItem()
        self.addItem(grid)

        self.scatter = None

    def update_pointcloud(self, points: np.ndarray, colors: np.ndarray):
        """points: (N,3) float32 XYZ, colors: (N,4) float32 RGBA (0-1)"""
        if self.scatter is None:
            self.scatter = gl.GLScatterPlotItem(pos=points, color=colors, size=3, pxMode=False)
            self.addItem(self.scatter)
        else:
            self.scatter.setData(pos=points, color=colors)
```

### Pitfalls
- Colors must be float32 [0–1] range with alpha
- Always subsample for performance
- Compute point cloud in background thread

---

## 2. Depth-RGB Camera Alignment (Kinect v1)

### Recommended Approach
**Manual alignment on the client** is simplest:
- `FREENECT_DEPTH_REGISTERED` does NOT work in Python bindings
- Use known/default extrinsics (baseline ~2.5 cm)
- Perform on client to save Pi CPU

### Standard Kinect v1 Values
```python
# Depth intrinsics
fx_d = 594.21
fy_d = 591.04
cx_d = 339.5
cy_d = 242.7

# RGB intrinsics
fx_rgb = 525
fy_rgb = 525
cx_rgb = 319.5
cy_rgb = 239.5

# Extrinsics
Tx = 0.025  # 2.5 cm baseline
```

### Code Example (Projection)
```python
# Project depth point to RGB coordinates
rgb_u = (x * fx_rgb / z) + cx_rgb + (Tx * fx_rgb / z)
rgb_v = (y * fy_rgb / z) + cy_rgb

# Filter valid projections
valid_rgb = (rgb_u >= 0) & (rgb_u < 640) & (rgb_v >= 0) & (rgb_v < 480)
colors = video_frame[rgb_v[valid_rgb].astype(int), rgb_u[valid_rgb].astype(int)]
```

### Pitfalls
- Slight per-device variation → acceptable for robotics
- Filter out-of-bounds projections
- Convert raw depth to mm if using standard formulas

---

## 3. ZMQ Reconnection Handling

### Recommended Approach
Use **zmq.Poller() with timeout** + **heartbeats**:
- Poller is more flexible than RCVTIMEO alone
- ZMQ auto-reconnects, but recv blocks forever → use non-blocking poll
- Heartbeats detect dead peers quickly

### Reconnection Logic
- Reuse sockets (no need to recreate)
- Exponential backoff on failed attempts
- Short timeout = hiccup, long no heartbeat = offline

### Code Example
```python
import zmq
from PyQt5.QtCore import QThread, pyqtSignal

class TelemetryThread(QThread):
    new_data = pyqtSignal(object)

    def __init__(self, robot_ip):
        super().__init__()
        self.robot_ip = robot_ip
        self.running = True

    def run(self):
        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.setsockopt(zmq.SUBSCRIBE, b'')
        subscriber.connect("tcp://{}:5559".format(self.robot_ip))

        poller = zmq.Poller()
        poller.register(subscriber, zmq.POLLIN)

        while self.running:
            events = dict(poller.poll(timeout=500))  # 500ms timeout
            if subscriber in events:
                try:
                    compressed = subscriber.recv(flags=zmq.NOBLOCK)
                    data = decompress(compressed)
                    self.new_data.emit(data)
                except zmq.Again:
                    pass
            else:
                # Timeout → possible disconnect
                print("No data - checking connection...")

        subscriber.close()
        context.term()
```

### Pitfalls
- Use `zmq.NOBLOCK` after poll to avoid blocking
- High poll frequency → CPU use; 500–1000ms is fine
- Heartbeats every 1–2s ensure <2s disconnect detection

---

# Implementation Plan

Based on guidance, recommended order:

| Priority | Task | Effort | Confidence |
|----------|------|--------|------------|
| 1 | Add `pyqtgraph` dependency | 5 min | 🟢 High |
| 2 | Create PointCloudWidget | 30 min | 🟢 High |
| 3 | Wire "Cloud Point" radio button | 20 min | 🟢 High |
| 4 | Add ZMQ poller timeout | 30 min | 🟢 High |
| 5 | Improve depth-RGB alignment | 1 hr | 🟡 Medium |

## Dependencies to Add
```bash
pip install pyqtgraph PyOpenGL
```
