# Architecture Improvements

Preparatory refactoring to de-risk planned features and improve code quality.

> **Status:** ✅ Architecture Complete!
> **Quick Wins:** ✅ Completed
> **Central Config:** ✅ Completed
> **FrameProcessor:** ✅ Completed
> **ConnectionManager:** ✅ Completed

## Priority 1: Configuration Management

### Current Problem
Ports, timeouts, and calibration values are hardcoded across multiple files.

### Solution: Central Config Module

**Create `app/common/config.py`:**
```python
"""Central configuration for K.O.C robot."""
import os

class Config:
    # Network ports
    HELLO_PORT = int(os.environ.get('HELLO_PORT', 5556))
    BRICKPI_PORT = int(os.environ.get('BRICKPI_PORT', 5557))
    KINECT_PORT = int(os.environ.get('KINECT_PORT', 5558))
    TELEMETRY_PORT = int(os.environ.get('TELEMETRY_PORT', 5559))
    COMMAND_PORT = int(os.environ.get('COMMAND_PORT', 5560))

    # Timing
    BRICKPI_CLOCK = 0.1  # seconds
    HELLO_SLEEP = 1.0

    # Kinect calibration (for point cloud)
    KINECT_FX = 594.21  # focal length x
    KINECT_FY = 591.04  # focal length y
    KINECT_CX = 339.5   # principal point x
    KINECT_CY = 242.7   # principal point y

    # Depth processing
    DEPTH_MAX = 2047  # 11-bit max
    DEPTH_MIN_VALID = 400  # ~0.5m
    DEPTH_MAX_VALID = 4000  # ~4m
```

**Benefits:**
- Single place to tune parameters
- Easy to override via environment
- Kinect calibration centralized for point cloud feature

**Files to update:** `server.py`, `gui.py`, `MainWindowWrapper.py`, `KinectProcess.py`

---

## Priority 2: Extract Frame Processing

### Current Problem
`MainWindowWrapper.update_kinect()` mixes:
- Frame reception
- Image processing (depth normalization)
- UI updates
- Numpy import inside method (!)

### Solution: Separate FrameProcessor Class

**Create `app/client/frame_processor.py`:**
```python
"""Frame processing utilities for Kinect data."""
import numpy as np
from PyQt5.QtGui import QImage

class FrameProcessor:
    """Converts raw Kinect data to displayable images."""

    @staticmethod
    def video_to_qimage(video_frame: np.ndarray) -> QImage:
        """Convert RGB video frame to QImage."""
        height, width, _ = video_frame.shape
        bytes_per_line = 3 * width
        return QImage(video_frame.data, width, height,
                      bytes_per_line, QImage.Format_RGB888)

    @staticmethod
    def depth_to_qimage(depth_array: np.ndarray,
                        colormap: str = 'grayscale') -> QImage:
        """Convert depth array to displayable QImage."""
        depth_normalized = np.clip(depth_array, 0, 2**10 - 1)
        depth_8bit = (depth_normalized >> 2).astype(np.uint8)
        depth_8bit = np.ascontiguousarray(depth_8bit)

        height, width = depth_8bit.shape
        return QImage(depth_8bit.data, width, height,
                      width, QImage.Format_Grayscale8)

    @staticmethod
    def depth_to_pointcloud(depth_array: np.ndarray,
                            fx: float, fy: float,
                            cx: float, cy: float) -> np.ndarray:
        """Convert depth to XYZ point cloud."""
        height, width = depth_array.shape

        # Create pixel coordinate grids
        u = np.arange(width)
        v = np.arange(height)
        u, v = np.meshgrid(u, v)

        # Convert to 3D coordinates
        z = depth_array.astype(np.float32)
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy

        # Stack into Nx3 array
        points = np.stack([x, y, z], axis=-1)
        return points.reshape(-1, 3)
```

**Benefits:**
- Point cloud logic ready to use
- Easy to add colormaps for depth
- Testable in isolation
- `MainWindowWrapper` stays clean

---

## Priority 3: Connection State Machine

### Current Problem
Connection state is implicit (button disabled = connected).
No way to disconnect, reconnect, or show errors.

### Solution: ConnectionManager Class

**Create `app/client/connection_manager.py`:**
```python
"""Manages robot connection lifecycle."""
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class ConnectionManager(QObject):
    state_changed = pyqtSignal(ConnectionState)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._state = ConnectionState.DISCONNECTED
        self._robot_ip = None
        self._telemetry_client = None
        self._command_client = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    def connect(self, robot_ip: str):
        """Initiate connection to robot."""
        self._state = ConnectionState.CONNECTING
        self.state_changed.emit(self._state)
        # ... start clients ...

    def disconnect(self):
        """Disconnect from robot."""
        # ... stop clients ...
        self._state = ConnectionState.DISCONNECTED
        self.state_changed.emit(self._state)
```

**Benefits:**
- Clean disconnect/reconnect support
- UI can bind to state changes
- Error handling centralized
- Enables connection status indicator

---

## Priority 4: Type Hints & Dataclasses

### Current Problem
Packet classes use manual `@property` boilerplate.
No type hints make IDE support poor.

### Solution: Use Dataclasses

**Before:**
```python
class LegoMotor:
    def __init__(self, port=None, speed=0, desired_speed=0, angle=0):
        self._port = port
        self._speed = speed
        # ... 20 more lines of properties ...
```

**After:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class LegoMotor:
    port: Optional[int] = None
    speed: int = 0
    desired_speed: int = 0
    angle: int = 0
```

**Benefits:**
- Less code
- Automatic `__repr__`, `__eq__`
- Better IDE autocomplete
- Easier to add new fields

**Risk:** Pickle compatibility — test serialization before/after!

---

## Priority 5: Logging Improvements

### Current Problem
- Inconsistent log levels
- No way to filter by component
- Debug logs always on or off globally

### Solution: Structured Logging

**Update `logging.yml`:**
```yaml
loggers:
  app.client:
    level: INFO
  app.client.gui:
    level: WARNING  # Reduce GUI noise
  app.server:
    level: DEBUG
  app.server.KinectProcess:
    level: INFO  # Reduce frame spam
```

---

## Implementation Order

| Order | Change | Effort | Impact | Enables |
|-------|--------|--------|--------|---------|
| 1 | Central Config | 1-2 hrs | Medium | All features, easier testing |
| 2 | FrameProcessor | 2-3 hrs | High | Point cloud, depth colormaps |
| 3 | ConnectionManager | 3-4 hrs | High | Disconnect, status indicator |
| 4 | Dataclasses | 2-3 hrs | Medium | Cleaner code, fewer bugs |
| 5 | Logging config | 30 min | Low | Debugging |

---

## Quick Wins ✅ COMPLETED

These take <30 minutes and improve quality immediately:

### 1. Move numpy import to top of file ✅
```python
# MainWindowWrapper.py - move to top
import numpy as np
```

### 2. Add `requirements.txt` ✅
```
numpy
pyzmq
PyQt5
pyyaml
netifaces
python-dotenv  # optional
```

### 3. Remove unused imports (optional)
Run: `pip install autoflake && autoflake --in-place --remove-all-unused-imports app/**/*.py`

### 4. Add `.editorconfig` (optional)
```ini
root = true

[*.py]
indent_style = space
indent_size = 4
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
```

---

## Recommendation

**Before implementing Point Cloud or Depth Alignment:**
1. ✅ Do Quick Wins (30 min)
2. ✅ Create `config.py` (1 hr)
3. ✅ Extract `FrameProcessor` (2 hrs)

This gives you:
- Centralized Kinect calibration parameters
- Point cloud conversion ready to use
- Clean separation for testing depth algorithms

**Before implementing Disconnect/Status Indicator:**
1. ✅ Create `ConnectionManager` (3 hrs)

This gives you:
- State machine for connection lifecycle
- Foundation for all GUI connection features

