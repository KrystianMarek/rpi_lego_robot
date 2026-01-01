# 3D Scene Reconstruction Feature - Implementation Plan

## Overview

This document outlines the plan to implement a 3D scene reconstruction feature that creates a composed 3D model of the observed environment by combining:
- Point cloud data from the Kinect sensor
- Object detection from video stream
- Turret rotation and robot movement tracking
- Multiple viewpoint fusion

The result will be a navigable 3D scene rendered in a new dedicated tab in the GUI client, composed of individually detected and modeled objects.

---

## ✅ CRITICAL BUG FIXED (2026-01-01)

**Issue**: Code was treating raw Kinect depth as metric distance, but raw values are **disparity**.

**Resolution**: Implemented proper depth conversion in `app/client/frame_processor.py`:
- Added `raw_depth_to_meters()` function using tangent-based formula
- Added `get_valid_depth_mask()` helper function
- Updated `depth_to_pointcloud()` and `depth_to_colored_pointcloud()` to use conversion
- Added `DEPTH_MIN_METERS` and `DEPTH_MAX_METERS` to `Config` (0.4m - 4.0m range)
- Updated `pointcloud_widget.py` camera/grid settings for meter coordinates

**Files modified**:
- `app/client/frame_processor.py` - depth conversion implementation
- `app/client/pointcloud_widget.py` - camera settings for meters
- `app/common/config.py` - added metric depth range constants

---

## Robot Physical Configuration

Based on inspection of the robot (see `pictures/pic1.jpg`, `pictures/pic2.jpg`):

```
                    ┌─────────────────┐
                    │  Xbox 360 Kinect │  ← Mounted on turret, elevated
                    │  (RGB + Depth)   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │     Turret      │  ← Rotates on lazy susan platform
                    │  (LEGO Technic) │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │    White Circular Platform       │  ← Rotation bearing
            │         (Lazy Susan)             │
            └────────────────┬────────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │              Main Robot Body                     │
    │  ┌─────────┐                      ┌─────────┐   │
    │  │ BrickPi │                      │Ultrasonic│   │  ← Fixed to body, front-facing
    │  │ (blue)  │                      │ Sensor   │   │     Does NOT move with turret!
    │  └─────────┘                      └─────────┘   │
    │           Multi-level LEGO Technic Frame        │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │              Caterpillar Tracks                  │
    │  ╔═══════════════════════════════════════════╗  │
    │  ║ Left Track                   Right Track  ║  │  ← Differential drive
    │  ╚═══════════════════════════════════════════╝  │
    └─────────────────────────────────────────────────┘
```

**Key Points:**
- **Kinect** is mounted HIGH on the turret structure (significant vertical offset)
- **Turret** rotates independently of robot body via geared motor
- **Ultrasonic sensor** is FIXED to robot body (front-facing), does NOT rotate with turret
- **Caterpillar tracks** provide differential drive (tank-style steering)
- **All motors** use gear reductions - encoder values need calibration factors

---

## Current State Analysis

### What We Have

#### Point Cloud Data Pipeline
```
Server (RPi)                          Client (PC)
┌─────────────────┐                  ┌──────────────────────┐
│ KinectProcess   │                  │ TelemetryClient      │
│ ├─ get_video()  │  KinectPacket    │ ├─ kinect_signal     │
│ ├─ get_depth()  │ ───────────────→ │ └─ decompress()      │
│ └─ libfreenect  │  ZMQ PUB/SUB     │                      │
└─────────────────┘                  └──────────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────────┐
                                     │ FrameProcessor       │
                                     │ ├─ depth_to_pointcloud()
                                     │ └─ Kinect intrinsics │
                                     └──────────────────────┘
                                              │
                                              ▼
                                     ┌──────────────────────┐
                                     │ PointCloudWidget     │
                                     │ ├─ pyqtgraph OpenGL  │
                                     │ └─ GLScatterPlotItem │
                                     └──────────────────────┘
```

#### Available Telemetry Data
| Data Source | Current Usage | Relevant for 3D | Notes |
|-------------|---------------|-----------------|-------|
| Video Frame (640×480 RGB) | Display only | Object detection input | |
| Depth Array (640×480, 11-bit) | Point cloud visualization | 3D reconstruction | |
| Turret Encoder | LCD display | Viewpoint rotation tracking | Needs gear ratio calibration |
| Left/Right Wheel Encoders | LCD display | Robot position estimation | Needs gear ratio calibration |
| Ultrasonic Sensor | LCD display | ⚠️ Limited use | Fixed to body, not turret - only useful when robot faces target |

#### Kinect Camera Parameters (from `config.py`)
- Focal lengths: fx=594.21, fy=591.04 pixels (default Kinect values - **confirmed reliable for starters**)
- Principal point: cx=339.5, cy=242.7 pixels (default Kinect values - **confirmed reliable for starters**)
- Valid depth range: 300-1800 (raw units) → approximately 0.4-2m in real distance
- Subsample stride: 2 (every 2nd pixel)

#### ✅ DEPTH CONVERSION (FIXED)
Proper depth conversion now implemented in `frame_processor.py`:
```python
# FIXED - raw_depth_to_meters() function
distance_m = 0.1236 * np.tan(raw / 2842.5 + 1.1863)
```
Point clouds are now in **meters**, not raw disparity units.

### What We're Missing

1. **Object Detection** - No ML model integration for detecting objects in video
2. **Pose Estimation** - No odometry/SLAM for tracking robot position
3. **Point Cloud Registration** - No alignment of multiple viewpoint captures
4. **Object Segmentation** - No separation of detected objects from background
5. **Mesh Generation** - No point cloud to mesh conversion
6. **Scene Management** - No data structure for 3D scene with multiple objects
7. **Persistent Storage** - No saving/loading of reconstructed scenes

---

## Architecture Design

### High-Level Data Flow

```
                                    ┌─────────────────────────────────────────────┐
                                    │           NEW: Scene Reconstruction         │
                                    │                  Pipeline                   │
                                    └─────────────────────────────────────────────┘
                                                         │
┌──────────────┐    ┌────────────────┐    ┌─────────────▼────────────┐
│ KinectPacket │───→│ FrameProcessor │───→│ ObjectDetector          │
│  • video     │    │  • point cloud │    │  • YOLO/MobileNet/etc   │
│  • depth     │    │  • RGB image   │    │  • bounding boxes       │
└──────────────┘    └────────────────┘    │  • object classes       │
                                          └─────────────┬────────────┘
                                                        │
┌──────────────┐                          ┌─────────────▼────────────┐
│ Telemetry    │─────────────────────────→│ PoseEstimator           │
│  • turret    │                          │  • robot position       │
│  • encoders  │                          │  • turret angle         │
└──────────────┘                          │  • camera transform     │
                                          └─────────────┬────────────┘
                                                        │
                                          ┌─────────────▼────────────┐
                                          │ ObjectSegmentor          │
                                          │  • extract object points │
                                          │  • filter by bbox        │
                                          │  • depth clustering      │
                                          └─────────────┬────────────┘
                                                        │
                                          ┌─────────────▼────────────┐
                                          │ PointCloudRegistration   │
                                          │  • ICP alignment         │
                                          │  • transform to world    │
                                          │  • merge observations    │
                                          └─────────────┬────────────┘
                                                        │
                                          ┌─────────────▼────────────┐
                                          │ SceneManager             │
                                          │  • object instances      │
                                          │  • merged point clouds   │
                                          │  • optional meshing      │
                                          └─────────────┬────────────┘
                                                        │
                                          ┌─────────────▼────────────┐
                                          │ SceneViewer3D (New Tab)  │
                                          │  • 3D rendered scene     │
                                          │  • object highlighting   │
                                          │  • navigation controls   │
                                          └──────────────────────────┘
```

### Proposed Module Structure

```
app/
├── common/
│   ├── calibration.py              # NEW: Calibration data classes
│   └── config.py                   # Existing, add calibration loading
├── client/
│   ├── scene_reconstruction/       # NEW PACKAGE
│   │   ├── __init__.py
│   │   ├── object_detector.py      # ML-based object detection
│   │   ├── pose_estimator.py       # Robot/turret pose tracking
│   │   ├── point_cloud_segmentor.py # Object point cloud extraction
│   │   ├── point_cloud_registrar.py # Multi-view alignment
│   │   ├── scene_manager.py        # Scene graph and object management
│   │   ├── mesh_generator.py       # Point cloud to mesh (optional)
│   │   └── models/                 # Pre-trained ML models
│   │       └── .gitkeep
│   └── gui/
│       ├── scene_viewer_widget.py  # NEW: 3D scene viewer
│       └── main_window.py          # Add new tab

tools/                              # NEW DIRECTORY
├── calibration_wizard.py           # Interactive calibration tool
├── kinect_depth_calibration.py     # Depth validation utility
└── encoder_calibration.py          # Wheel/turret encoder calibration

data/
└── calibration.yaml                # Calibration values (gitignored template)
```

---

## Implementation Phases

### Phase 0: Calibration and Measurement
**Estimated effort: 1-2 days**

**Critical prerequisite** - Without accurate calibration, pose estimation and point cloud alignment will fail.

#### 0.1 Why Calibration is Needed

All motors in the robot use **gear reductions**, meaning:
- Raw encoder ticks ≠ actual wheel/turret rotation
- We need to determine the gear ratios experimentally
- Kinect depth values need conversion (non-linear!) to real distance

#### 0.2 Calibration Procedures

##### A. Kinect Depth Calibration

**Goal**: Convert raw Kinect depth values to metric distance (meters).

**⚠️ CRITICAL**: Raw depth is **NON-LINEAR** (disparity, not distance). Use one of these formulas:

```python
# Option 1: Tangent-based formula (recommended)
distance_m = 0.1236 * np.tan(raw_depth / 2842.5 + 1.1863)

# Option 2: Inverse formula
distance_m = 1.0 / (raw_depth * -0.0030711016 + 3.3309495161)
```

**Procedure**:
1. **Wait 5-10 minutes** for Kinect to warm up (temperature affects depth!)
2. Place a flat surface (wall/board) perpendicular to Kinect at known distances
3. Measure with tape measure: **50cm, 80cm, 100cm, 150cm, 200cm** from Kinect
4. Record raw depth values (center region average) at each distance
5. Fit polynomial curve to your data (factory variations exist between units)
6. **Mask invalid values**: raw depth 0 or 2047 = invalid, must filter out

**Expected accuracy** (per guidance):
| Distance | Expected Error |
|----------|----------------|
| 0.5-1.0m | ±1-3mm |
| 2.0m | ±1-2cm |
| 3.0m+ | ±4-5cm |

**Expected output**:
```python
# app/common/calibration.py - depth conversion
def raw_depth_to_meters(raw_depth: np.ndarray) -> np.ndarray:
    """Convert raw Kinect depth to meters using calibrated formula."""
    # Mask invalid values
    valid = (raw_depth > 0) & (raw_depth < 2047)

    distance_m = np.zeros_like(raw_depth, dtype=np.float32)
    distance_m[valid] = 0.1236 * np.tan(raw_depth[valid] / 2842.5 + 1.1863)
    distance_m[~valid] = np.nan  # Mark invalid

    return distance_m
```

**Additional considerations**:
- **Temperature drift**: Kinect depth decreases by <2mm as sensor warms up
- **Recalibrate** if ambient temperature changes >10°C
- **Update pipeline immediately** after capture to convert to meters

**Calibration utility** (to create):
```python
# tools/kinect_depth_calibration.py
class KinectDepthCalibrator:
    """Records depth samples at known distances for calibration."""

    def __init__(self):
        self.samples = []  # (known_distance_m, raw_depth_avg)

    def wait_for_warmup(self, minutes: int = 10):
        """Display countdown timer for Kinect warm-up."""

    def record_sample(self, known_distance_m: float):
        """Capture depth frame and record center region average."""

    def compute_calibration(self) -> dict:
        """Fit polynomial to samples, compare with standard formulas."""

    def validate_calibration(self) -> dict:
        """Test calibration accuracy at intermediate distances."""

    def save_calibration(self, filepath: str):
        """Export calibration to config file."""
```

##### B. Wheel Encoder Calibration (Track Distance)

**Goal**: Determine encoder ticks per mm of robot travel.

**Procedure**:
1. Mark robot starting position on floor (use flat, non-slip surface)
2. Reset encoder values to 0
3. Drive robot forward in a straight line for **exactly 1 meter** (use tape measure)
4. Record final encoder values for both tracks
5. Repeat **5+ times** and average (gear ratios vary with wear)

**Calculation**:
```python
left_ticks_per_mm = average_left_encoder_ticks / 1000
right_ticks_per_mm = average_right_encoder_ticks / 1000
```

**Also measure**:
- Track-to-track distance (wheel base) for turning calculations
- Drive at 50cm, 100cm to verify linearity

**⚠️ Caterpillar Track Slip** (per guidance):
- Tracks slip more than wheels, especially during turns (up to 50% slip in pivots!)
- Straight-line travel is more reliable than turns
- Expected dead reckoning error: **10-20% over distance**

**Slip Detection** (implement in pose estimator):
```python
def check_for_slip(left_delta: int, right_delta: int) -> bool:
    """Detect track slip during straight-line travel."""
    if abs(left_delta - right_delta) / max(left_delta, right_delta) > 0.10:
        # >10% mismatch between tracks = likely slip
        return True
    return False
```

**Gear backlash warning**: LEGO geared motors have play; encoder readings may not update immediately on direction change. Account for this in calibration.

##### C. Turret Encoder Calibration

**Goal**: Determine encoder ticks per degree of turret rotation.

**Procedure**:
1. Align turret to a known forward position (use visual marker)
2. Reset turret encoder to 0
3. Rotate turret exactly **90°** (use protractor or right-angle reference)
4. Record encoder value
5. Repeat for 180°, 270°, 360°
6. Verify symmetry (clockwise vs counter-clockwise)
7. **Check backlash**: rotate CW then CCW and compare readings

**Calculation**:
```python
TURRET_ENCODER_TICKS_PER_DEG = encoder_ticks_at_90 / 90.0
```

**⚠️ Turret Homing** (recommended per guidance):
Encoder drift from gear backlash accumulates over time. Implement homing at scan start:

```python
# Option 1: Software reference (mark on robot body)
def home_turret(self):
    """Rotate turret to visual reference position and reset encoder."""
    # User manually aligns to marker, then calls this
    self._turret_encoder_offset = current_encoder_value

# Option 2: Limit switch (hardware, if available)
def home_turret_hardware(self):
    """Rotate until limit switch triggered, then reset."""
```

**Best practice**: Always home turret before starting a new scan session.

##### D. Kinect Mount Position Measurement

**Goal**: Measure Kinect position relative to robot center for coordinate transforms.

**Measurements needed** (use ruler/calipers):
```python
# All in meters (use meters for numerical stability per guidance)
# Relative to robot center (track midpoint on floor)
KINECT_MOUNT_X = 0.0      # Lateral offset (0 if centered)
KINECT_MOUNT_Y = TBD      # Height above floor (significant! ~0.15-0.20m based on photos)
KINECT_MOUNT_Z = TBD      # Forward offset from robot center
KINECT_TILT_DEG = TBD     # Downward tilt angle (5-10° typical for floor visibility)
```

**Measuring the tilt angle**:
1. Place Kinect facing a wall at known distance
2. Note where center of depth frame hits the wall
3. Calculate angle from offset: `tilt_deg = arctan(vertical_offset / distance)`

**⚠️ RGB-Depth Camera Offset** (per guidance):
Kinect v1 has ~2.5cm physical offset between RGB and IR/depth cameras. This causes color-depth misalignment at object edges. Options:
1. **Ignore** (acceptable for depth-colored point clouds)
2. **Remap RGB to depth space** using Kinect intrinsics/extrinsics (more complex)

#### 0.3 Calibration Data Storage

Create `app/common/calibration.py`:
```python
@dataclass
class RobotCalibration:
    """Stores all calibration parameters."""

    # Kinect depth
    kinect_depth_scale: float = 1.0
    kinect_depth_offset: float = 0.0

    # Wheel encoders
    left_encoder_ticks_per_mm: float = 1.0
    right_encoder_ticks_per_mm: float = 1.0
    track_width_mm: float = 150.0  # Distance between tracks

    # Turret
    turret_encoder_ticks_per_deg: float = 1.0
    turret_zero_offset: int = 0  # Encoder value at "forward" position

    # Kinect mount
    kinect_mount_x_mm: float = 0.0
    kinect_mount_y_mm: float = 200.0
    kinect_mount_z_mm: float = 50.0
    kinect_tilt_deg: float = 0.0

    @classmethod
    def load(cls, filepath: str) -> 'RobotCalibration':
        """Load from YAML/JSON file."""

    def save(self, filepath: str):
        """Save to YAML/JSON file."""
```

#### 0.4 Calibration Utility Tool

Create `tools/calibration_wizard.py` - GUI or CLI tool that:
1. Guides user through each calibration step
2. Records measurements automatically where possible
3. Validates results (e.g., left/right encoder should be similar)
4. Exports calibration file

---

### Phase 1: Foundation - Object Detection Integration
**Estimated effort: 2-3 days**

#### 1.1 Object Detector Module
Create `app/client/scene_reconstruction/object_detector.py`:

```python
# Conceptual interface
class ObjectDetector:
    """Detects objects in video frames using ML model."""

    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """Load detection model (YOLO, MobileNet-SSD, etc.)"""

    def detect(self, video_frame: np.ndarray) -> List[Detection]:
        """
        Run object detection on frame.

        Returns:
            List of Detection(bbox, class_name, confidence, mask)
        """

    @property
    def supported_classes(self) -> List[str]:
        """List of detectable object classes."""
```

**Model Options (prioritized):**
1. **YOLOv8-nano** - Fast, accurate, good for real-time (~30ms inference)
2. **MobileNet-SSD** - Lightweight, works well on CPU
3. **Detectron2** - More accurate, heavier (if GPU available)

**Dependencies to add:**
```
# requirements/client.txt additions
ultralytics>=8.0.0  # YOLOv8
# OR
opencv-python>=4.8.0  # includes DNN module for MobileNet-SSD
```

#### 1.2 Detection Data Classes
```python
@dataclass
class BoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

@dataclass
class Detection:
    bbox: BoundingBox
    class_name: str
    confidence: float
    instance_id: Optional[int] = None
    mask: Optional[np.ndarray] = None  # For instance segmentation
```

#### 1.3 Integration Point
Modify `MainWindowWrapper.update_kinect()` to optionally run detection:
- Add toggle in UI to enable/disable detection
- Display bounding boxes on video stream overlay
- Pass detections to scene reconstruction pipeline

---

### Phase 2: Pose Estimation and Tracking
**Estimated effort: 2-3 days**

#### 2.1 Pose Estimator Module
Create `app/client/scene_reconstruction/pose_estimator.py`:

```python
class PoseEstimator:
    """Tracks robot and turret pose for point cloud transformation."""

    def __init__(self, wheel_base: float, encoder_ticks_per_rev: int):
        """Initialize with robot physical parameters."""

    def update(self, telemetry: TelemetryPacket):
        """Update pose from encoder readings."""

    def get_camera_transform(self) -> np.ndarray:
        """
        Get 4x4 transformation matrix from camera to world coordinates.
        Combines: robot_position × robot_rotation × turret_rotation × kinect_mount
        """

    def reset(self):
        """Reset pose to origin (for scene reconstruction start)."""
```

**Key considerations:**
- Encoder-based odometry is drift-prone - accumulate errors over time
- Turret angle should be more reliable (direct motor encoder, but has backlash)
- Dead reckoning works for ~5 minute sessions on flat surfaces (per guidance)
- Expected error: **10-20% over distance** due to track slip

**Additional features to implement** (per guidance):

```python
class PoseEstimator:
    def check_slip(self, left_delta: int, right_delta: int) -> bool:
        """Detect slip: >5-10% L/R mismatch during straight travel."""

    def home_turret(self):
        """Reset turret to known position at scan start."""

    def get_odometry_confidence(self) -> float:
        """Return 0-1 confidence based on slip detection history."""
```

**Future enhancement**: Add visual odometry using ORB features on RGB frames for drift correction (see Future Enhancements section)

#### 2.2 Coordinate System Definition
```
World Frame (Right-handed):
    Y (up)
    │
    │
    └────── X (right)
   /
  Z (forward - robot facing direction at start)

Robot Frame:
  - Origin at robot center
  - X: right, Y: up, Z: forward

Turret Frame:
  - Rotates around Y axis relative to robot

Kinect Frame:
  - Mounted on turret
  - Looking along +Z (depth direction)
```

#### 2.3 Configuration Parameters

**Note**: These values come from **Phase 0: Calibration** - do not guess!

```python
# Load from calibration file (see Phase 0)
from app.common.calibration import RobotCalibration

calibration = RobotCalibration.load('calibration.yaml')

# Example calibration values (MUST BE MEASURED):
# calibration.left_encoder_ticks_per_mm = TBD   # From wheel calibration
# calibration.right_encoder_ticks_per_mm = TBD  # From wheel calibration
# calibration.track_width_mm = TBD              # Physical measurement
# calibration.turret_encoder_ticks_per_deg = TBD  # From turret calibration
# calibration.kinect_mount_y_mm = TBD           # Height measurement (significant!)
# calibration.kinect_mount_z_mm = TBD           # Forward offset measurement
```

**Important**: The Kinect is mounted HIGH on the turret (estimated 15-20cm above robot body based on photos). This vertical offset significantly affects point cloud world positioning.

---

### Phase 3: Point Cloud Segmentation and Object Extraction
**Estimated effort: 2-3 days**

#### 3.1 Point Cloud Segmentor Module
Create `app/client/scene_reconstruction/point_cloud_segmentor.py`:

```python
class PointCloudSegmentor:
    """Extracts object point clouds using detection bounding boxes."""

    def segment_by_bbox(
        self,
        points: np.ndarray,        # Full point cloud (N, 3)
        colors: np.ndarray,        # Point colors (N, 4)
        detection: Detection,      # Object detection with bbox
        depth_array: np.ndarray    # Original depth for projection
    ) -> ObjectPointCloud:
        """
        Extract points belonging to detected object.

        Steps:
        1. Project 3D points back to 2D pixel coordinates
        2. Filter points within bounding box
        3. Apply depth clustering to separate foreground object
        4. Return isolated object point cloud
        """

    def segment_by_mask(
        self,
        points: np.ndarray,
        colors: np.ndarray,
        detection: Detection,  # With instance segmentation mask
    ) -> ObjectPointCloud:
        """More precise segmentation using instance mask."""
```

#### 3.2 Object Point Cloud Data Class
```python
@dataclass
class ObjectPointCloud:
    points: np.ndarray           # (M, 3) XYZ in camera frame
    colors: np.ndarray           # (M, 4) RGBA
    class_name: str
    confidence: float
    centroid: np.ndarray         # (3,) center point
    bbox_3d: Optional[np.ndarray]  # (8, 3) 3D bounding box corners
    observation_count: int = 1   # Number of viewpoints merged
```

#### 3.3 Pre-processing Pipeline (NEW - per guidance)

**Always apply before segmentation:**
```python
def preprocess_pointcloud(points: np.ndarray, colors: np.ndarray) -> tuple:
    """Clean point cloud before segmentation."""

    # 1. Remove invalid points (NaN from invalid depth)
    valid_mask = ~np.isnan(points).any(axis=1)

    # 2. Statistical outlier removal (Open3D)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points[valid_mask])
    pcd, inlier_idx = pcd.remove_statistical_outlier(
        nb_neighbors=20,
        std_ratio=2.0
    )

    return np.asarray(pcd.points), colors[valid_mask][inlier_idx]
```

#### 3.4 Depth Clustering Algorithm
For separating foreground objects from background within bbox:
1. **DBSCAN clustering** on depth values within bbox region
2. Select cluster closest to camera (smallest depth)
3. Remove outliers using statistical filtering

**⚠️ Depth Shadow Handling** (per guidance):
Kinect v1 has notorious depth shadows at object edges (invalid regions where IR is occluded).

```python
def handle_depth_shadows(depth_array: np.ndarray, bbox: BoundingBox) -> np.ndarray:
    """Detect and handle depth shadows within bounding box."""

    # 1. Identify shadow regions (invalid depth surrounded by valid)
    shadow_mask = (depth_array == 0) | (depth_array == 2047)

    # 2. Option A: Mark as invalid and exclude from clustering
    # 3. Option B: Inpaint using nearest-neighbor interpolation

    # 4. Use depth gradient to refine edges (threshold >50-100 raw units)
    gradient = np.gradient(depth_array)
    edge_mask = np.abs(gradient[0]) + np.abs(gradient[1]) > 75

    return cleaned_depth
```

**For objects at similar depths** (e.g., object on table):
- DBSCAN may fail to separate; consider incorporating:
  - Color differences (RGB-DBSCAN)
  - Surface normals
  - Instance segmentation masks (YOLOv8-seg)

---

### Phase 4: Multi-View Point Cloud Registration
**Estimated effort: 3-4 days**

#### 4.1 Point Cloud Registrar Module
Create `app/client/scene_reconstruction/point_cloud_registrar.py`:

```python
class PointCloudRegistrar:
    """Aligns and merges point clouds from different viewpoints."""

    def __init__(self):
        self._global_cloud = None
        self._object_clouds: Dict[int, ObjectPointCloud] = {}

    def transform_to_world(
        self,
        object_cloud: ObjectPointCloud,
        camera_transform: np.ndarray  # 4x4 matrix
    ) -> ObjectPointCloud:
        """Transform object point cloud from camera to world frame."""

    def register_object(
        self,
        new_cloud: ObjectPointCloud,
        object_id: int
    ):
        """
        Add/merge object observation to scene.

        If object_id exists:
          - Use ICP to align new observation
          - Merge points, removing duplicates
          - Update confidence and observation count
        Else:
          - Add as new object instance
        """

    def get_merged_scene(self) -> SceneData:
        """Return all registered objects in world coordinates."""
```

#### 4.2 Registration Algorithm Options

**Recommended approach** (per guidance):

1. **Point-to-Plane ICP** (preferred over point-to-point)
   - Better convergence for noisy/smooth surfaces
   - Requires computing normals first

2. **Multi-scale ICP** for better initialization tolerance
   - Voxel sizes: `[0.05, 0.025, 0.0125]` meters

3. **Global Registration (RANSAC)** if angle difference >45°
   - Use before ICP when poses are unreliable

4. **Colored ICP** - 20-50% better alignment for textured scenes

**Concrete Parameters** (per guidance):

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| `max_correspondence_distance` | 0.05-0.1m | Start with 0.05m, increase if init poor |
| `voxel_size` for downsampling | 0.02m | Range 0.01-0.05m depending on object size |
| `fitness` threshold | < 0.5 = failure | Also check RMSE > 0.02m |
| Multi-scale voxels | [0.05, 0.025, 0.0125] | Coarse to fine |

**Library: Open3D**
```python
import open3d as o3d

def icp_registration_point_to_plane(source, target, init_transform, threshold=0.05):
    """Point-to-plane ICP with failure detection."""

    # Compute normals (required for point-to-plane)
    source.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=0.1, max_nn=30))
    target.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
        radius=0.1, max_nn=30))

    result = o3d.pipelines.registration.registration_icp(
        source, target, threshold, init_transform,
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPlane()
    )

    # Failure detection
    if result.fitness < 0.5 or result.inlier_rmse > 0.02:
        raise RegistrationFailedError(
            f"ICP failed: fitness={result.fitness:.2f}, rmse={result.inlier_rmse:.3f}")

    return result.transformation

def multi_scale_icp(source, target, init_transform):
    """Multi-scale ICP for better init tolerance."""
    voxel_sizes = [0.05, 0.025, 0.0125]
    max_iters = [50, 30, 20]

    current_transform = init_transform
    for voxel_size, max_iter in zip(voxel_sizes, max_iters):
        source_down = source.voxel_down_sample(voxel_size)
        target_down = target.voxel_down_sample(voxel_size)

        # ... run ICP at this scale
        current_transform = icp_result.transformation

    return current_transform
```

**Dependencies to add:**
```
# requirements/client.txt additions
open3d>=0.17.0
```

**When ICP fails**:
- Log the failure with fitness/RMSE values
- Skip this frame and wait for better observation
- Consider global registration (RANSAC) as fallback

---

### Phase 5: Scene Management
**Estimated effort: 2-3 days**

#### 5.1 Scene Manager Module
Create `app/client/scene_reconstruction/scene_manager.py`:

```python
class SceneManager:
    """Manages the reconstructed 3D scene with multiple objects."""

    def __init__(self):
        self._objects: Dict[int, SceneObject] = {}
        self._next_object_id: int = 0
        self._scene_bounds: BoundingBox3D = None

    def add_observation(
        self,
        detections: List[Detection],
        point_cloud: np.ndarray,
        camera_transform: np.ndarray
    ):
        """
        Process new frame observation.

        Steps:
        1. Match detections to existing objects (tracking)
        2. Segment point clouds for each detection
        3. Transform to world coordinates
        4. Merge with existing objects or create new
        """

    def get_scene_for_render(self) -> RenderableScene:
        """Get scene data optimized for 3D rendering."""

    def clear(self):
        """Reset scene to empty."""

    def save(self, filepath: str):
        """Export scene to file (PLY, OBJ, or custom format)."""

    def load(self, filepath: str):
        """Load previously saved scene."""
```

#### 5.2 Object Tracking (Cross-Frame Association)

**Concrete Parameters** (per guidance):
| Parameter | Value | Notes |
|-----------|-------|-------|
| Centroid distance threshold | 0.1-0.3m | Scale by object size |
| Split detection IoU | > 0.5 | Between new/old bbox |

```python
class ObjectTracker:
    """Associates detections across frames to track objects."""

    DEFAULT_DISTANCE_THRESHOLD = 0.2  # meters

    def match_detections(
        self,
        new_detections: List[Detection],
        existing_objects: Dict[int, SceneObject]
    ) -> Dict[int, int]:  # detection_idx -> object_id
        """
        Match detections to existing objects using:
        1. Class name match (must be same class)
        2. 3D centroid proximity (transformed to world)
        3. IoU of projected bounding boxes (for splitting detection)
        """

    def get_distance_threshold(self, detection: Detection) -> float:
        """Scale threshold by estimated object size from bbox."""
        bbox_size = max(detection.bbox.width, detection.bbox.height)
        # Larger objects get larger threshold
        return max(0.1, min(0.3, bbox_size * 0.001))
```

**Per guidance**: Our simple centroid-based approach is sufficient for static scenes with good poses. Upgrade to SORT (Simple Online Real-time Tracking) if mismatches occur frequently.

#### 5.3 Scene Data Classes
```python
@dataclass
class SceneObject:
    object_id: int
    class_name: str
    merged_cloud: np.ndarray      # (N, 3) world coordinates
    colors: np.ndarray            # (N, 4) RGBA
    centroid_world: np.ndarray    # (3,) center in world frame
    bbox_3d_world: np.ndarray     # (8, 3) oriented bounding box
    observations: int             # Number of merged viewpoints
    confidence: float             # Average detection confidence
    last_seen_time: float         # Timestamp of last observation

@dataclass
class RenderableScene:
    objects: List[SceneObject]
    floor_plane: Optional[np.ndarray]  # For context
    robot_path: List[np.ndarray]       # Robot trajectory
    scene_bounds: BoundingBox3D
```

---

### Phase 6: 3D Scene Viewer Widget
**Estimated effort: 3-4 days**

#### 6.1 Scene Viewer Widget
Create `app/client/gui/scene_viewer_widget.py`:

```python
class SceneViewerWidget(QWidget):
    """3D viewer for reconstructed scene with multiple objects."""

    def __init__(self, parent=None):
        # Use pyqtgraph OpenGL (consistent with PointCloudWidget)
        # OR consider vispy for more advanced rendering

    def set_scene(self, scene: RenderableScene):
        """Update displayed scene."""

    def highlight_object(self, object_id: int):
        """Highlight selected object in view."""

    def set_view_mode(self, mode: ViewMode):
        """Switch between: FREE_CAMERA, TOP_DOWN, FOLLOW_ROBOT"""

    # Rendering features:
    # - Per-object coloring (by class or random)
    # - Object labels floating above centroids
    # - 3D bounding boxes (wireframe)
    # - Floor grid
    # - Robot position indicator
    # - Camera frustum showing current view
```

#### 6.2 GUI Integration
Modify `main_window.py`:
```python
def _setup_video_tabs(self):
    # ... existing tabs ...

    # --- Tab 3: Scene Reconstruction (NEW) ---
    self.scene_tab = QtWidgets.QWidget()
    self.scene_tab.setObjectName("scene_tab")
    self.scene_layout = QtWidgets.QVBoxLayout(self.scene_tab)
    self.scene_layout.setContentsMargins(0, 0, 0, 0)

    # Control bar for scene reconstruction
    self.scene_controls = QtWidgets.QHBoxLayout()
    self.btn_start_scan = QtWidgets.QPushButton("Start Scan")
    self.btn_clear_scene = QtWidgets.QPushButton("Clear")
    self.btn_save_scene = QtWidgets.QPushButton("Save")
    self.lbl_object_count = QtWidgets.QLabel("Objects: 0")
    # ... add to layout ...

    self.video_tab_widget.addTab(self.scene_tab, "🏗️ 3D Scene")
```

#### 6.3 Control Flow
```
User clicks "Start Scan"
         │
         ▼
┌─────────────────────────────────┐
│ For each incoming KinectPacket: │
│ 1. Run object detection         │
│ 2. Update pose from telemetry   │
│ 3. Segment detected objects     │
│ 4. Transform to world frame     │
│ 5. Register/merge in scene      │
│ 6. Update 3D viewer            │
└─────────────────────────────────┘
         │
         ▼
User can rotate turret / move robot
to capture from different angles
         │
         ▼
Click "Stop Scan" when done
         │
         ▼
Export scene or continue viewing
```

---

### Phase 7: Mesh Generation (Optional Enhancement)
**Estimated effort: 2-3 days**

#### 7.1 Mesh Generator Module
Create `app/client/scene_reconstruction/mesh_generator.py`:

```python
class MeshGenerator:
    """Converts point clouds to triangle meshes."""

    def generate_mesh(
        self,
        point_cloud: np.ndarray,
        colors: np.ndarray,
        method: str = 'poisson'
    ) -> TriangleMesh:
        """
        Generate mesh from point cloud.

        Methods:
        - 'poisson': Poisson surface reconstruction (smooth)
        - 'ball_pivot': Ball pivoting algorithm (preserves detail)
        - 'alpha_shape': Alpha shape (for convex-ish objects)
        """
```

**When to mesh:**
- Only after sufficient observations (3+ viewpoints)
- On user request ("Generate Mesh" button)
- For export purposes

---

## Dependencies Summary

### New Python Packages

```
# requirements/client.txt additions

# Object Detection (choose one)
ultralytics>=8.0.0        # YOLOv8 - recommended
# OR torch + torchvision  # For PyTorch-based models

# Point Cloud Processing
open3d>=0.17.0            # Registration, meshing, visualization

# Optional enhancements
scikit-learn>=1.0.0       # DBSCAN clustering (may already have)
scipy>=1.10.0             # Spatial algorithms (may already have)
```

### Model Files
- YOLO weights: ~6MB (nano) to ~50MB (large)
- Store in `app/client/scene_reconstruction/models/`
- Add to `.gitignore` with download script

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Inaccurate calibration** | **Critical** | **Phase 0 is mandatory; validate with known test objects** |
| ~~Depth treated as linear~~ | ~~Critical~~ | ✅ **FIXED**: `raw_depth_to_meters()` implemented |
| Gear ratio variations | High | Multiple calibration runs; periodic recalibration |
| **Encoder backlash** | High | Implement turret homing; multiple calibration trials |
| Detection accuracy on diverse objects | High | Use pre-trained COCO model; allow user class filtering |
| Odometry drift causing misalignment | High | Implement slip detection; add visual odometry later |
| **Caterpillar track slip** | High | Up to 50% slip on turns; prefer straight-line scans |
| **ICP local minima** | High | Use multi-scale ICP; add global registration fallback |
| Kinect depth non-linearity | Medium | ~~Use polynomial fit~~ → Use standard formula + validation |
| **RGB-Depth offset (2.5cm)** | Medium | Ignore or remap RGB to depth space |
| **Kinect temperature drift** | Medium | 5-10min warm-up before scanning |
| **Depth shadows at edges** | Medium | Detect and exclude; or inpaint with nearest-neighbor |
| Performance bottleneck (detection) | Medium | Run detection on separate thread; skip frames if needed |
| Memory usage with large scenes | Medium | Voxel grid filtering on global scene |
| Complex coordinate transformations | Medium | Unit tests for each transform; use meters; right-handed |
| **Power/heat issues** | Medium | Monitor voltage; add cooling for long scans |
| **Motion blur** | Low | Limit robot speed during scanning |
| OpenGL compatibility issues | Low | Already using pyqtgraph successfully |

---

## Testing Strategy

### Unit Tests
```
tests/
├── test_object_detector.py      # Mock model, test bbox format
├── test_pose_estimator.py       # Known encoder values → expected pose
├── test_point_cloud_segmentor.py # Synthetic cloud with known objects
├── test_point_cloud_registrar.py # ICP on translated/rotated clouds
└── test_scene_manager.py        # Object tracking across frames
```

### Integration Tests
1. **End-to-end scan simulation**: Recorded telemetry + Kinect data
2. **Coordinate system validation**: Known object at known position
3. **Memory profiling**: Extended scan session

### Manual Testing
- Single stationary object from multiple angles
- Multiple objects at different distances
- Moving robot around room
- Edge cases: overlapping objects, partial views

---

## Implementation Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| **Phase 0: Calibration** | **1-2 days** | **Physical robot access required** |
| Phase 1: Object Detection | 2-3 days | None (parallel with Phase 0) |
| Phase 2: Pose Estimation | 2-3 days | **Phase 0** |
| Phase 3: Point Cloud Segmentation | 2-3 days | Phase 1 |
| Phase 4: Registration | 3-4 days | Phase 2, Phase 3 |
| Phase 5: Scene Management | 2-3 days | Phase 4 |
| Phase 6: 3D Viewer | 3-4 days | Phase 5 |
| Phase 7: Mesh Generation | 2-3 days | Phase 5 (optional) |

**Total estimated: 18-25 days** (with Phase 7)

```
                            ┌──────────────────┐
                            │ Phase 0:         │
                            │ Calibration      │ ◄─── MUST BE DONE FIRST (needs robot)
                            └────────┬─────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        │
   ┌────────────────┐      ┌────────────────┐                │
   │ Phase 1:       │      │ Phase 2:       │                │
   │ Object         │      │ Pose           │ ◄──────────────┘
   │ Detection      │      │ Estimation     │
   └────────┬───────┘      └────────┬───────┘
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
              ┌────────────────┐
              │ Phase 3:       │
              │ Segmentation   │
              └────────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │ Phase 4:       │
              │ Registration   │
              └────────┬───────┘
                       │
                       ▼
              ┌────────────────┐
              │ Phase 5:       │
              │ Scene Mgmt     │
              └────────┬───────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
   ┌────────────────┐    ┌────────────────┐
   │ Phase 6:       │    │ Phase 7:       │
   │ 3D Viewer      │    │ Meshing (opt)  │
   └────────────────┘    └────────────────┘
```

---

## Future Enhancements

1. **Visual Odometry**: Use feature matching between frames to improve pose estimation
2. **Loop Closure**: Detect when robot returns to previously seen area
3. **Semantic Segmentation**: Use per-pixel masks for more accurate object extraction
4. **Real-time SLAM**: Full SLAM integration for continuous localization
5. **AR Overlay**: Show reconstructed objects overlaid on live video
6. **Cloud Storage**: Save/share reconstructed scenes
7. **Object Recognition**: Identify specific objects (not just classes)

---

## Open Questions

1. ~~**Model selection**: YOLOv8-nano vs MobileNet-SSD for initial implementation?~~ → **Answered: Use Ultralytics YOLOv8**
2. **Detection frequency**: Every frame or skip frames for performance? → Guidance suggests 2-5 FPS by downsampling
3. **Scene persistence**: Auto-save or manual only?
4. ~~**Robot parameters**: Exact wheel base, encoder resolution, Kinect mount position?~~ → **Resolved: Phase 0 calibration**
5. **Expected scene size**: Max area to reconstruct? Max number of objects?

### Answered/Clarified (from Guidance Review)

| Question | Answer |
|----------|--------|
| Ultrasonic sensor for distance? | **No** - Fixed to body, doesn't rotate with Kinect. Only useful when entire robot faces target. |
| Encoder accuracy? | **Requires calibration** - All motors use gear reductions. 10-20% error expected from slip. |
| Kinect depth linear? | **NO!** - Raw depth is disparity (1/distance). Use tangent or inverse formula. |
| Kinect depth accuracy? | ±1-3mm at 0.5-1m, ±1-2cm at 2m, ±4-5cm at 3m+ |
| Default intrinsics reliable? | **Yes** - fx=594.21, fy=591.04, cx=339.5, cy=242.7 are fine for starters |
| Dead reckoning work for 5min? | **Yes** - On flat surfaces, but expect 10-20% drift |
| ICP parameters? | threshold=0.05-0.1m, voxel=0.02m, use point-to-plane, multi-scale |
| Point-to-point vs plane ICP? | **Point-to-plane** - better convergence, requires normals |
| Transform chain order? | **Correct**: T_world_robot @ T_robot_turret @ T_turret_kinect @ point |
| Units for transforms? | **Meters** - better numerical stability |
| Kinect warm-up needed? | **Yes** - 5-10 minutes before scanning |
| Object tracking approach? | **Centroid-based sufficient** for static scenes; upgrade to SORT if issues |
| RGB-Depth misalignment? | **2.5cm offset** - ignore or remap RGB to depth space |

---

## References

- [Open3D Documentation](http://www.open3d.org/docs/)
- [YOLOv8 by Ultralytics](https://docs.ultralytics.com/)
- [Point Cloud Registration Survey](https://arxiv.org/abs/2103.02857)
- [Kinect Sensor Calibration](https://openkinect.org/wiki/Imaging_Information)
- Internal: `doc/development/guidance-3d-reconstruction.md` - Expert review and parameter recommendations

---

## Appendix A: Robot Photos

Reference images showing robot configuration:
- `pictures/pic1.jpg` - Front-left view showing Kinect mount, turret, ultrasonic sensor
- `pictures/pic2.jpg` - Front-right view showing BrickPi, track system, gear mechanisms

---

## Appendix B: Quick Reference - Key Parameters

From expert guidance review, use these starting values:

```python
# === Kinect Depth Conversion ===
def raw_to_meters(raw):
    return 0.1236 * np.tan(raw / 2842.5 + 1.1863)

# === ICP Registration ===
ICP_MAX_CORRESPONDENCE_DIST = 0.05  # meters
ICP_VOXEL_SIZE = 0.02               # meters
ICP_MULTI_SCALE_VOXELS = [0.05, 0.025, 0.0125]
ICP_FITNESS_THRESHOLD = 0.5         # below = failure
ICP_RMSE_THRESHOLD = 0.02           # above = failure

# === Object Tracking ===
TRACKING_DISTANCE_THRESHOLD = 0.2   # meters (scale by object size)

# === Slip Detection ===
SLIP_THRESHOLD = 0.10  # 10% L/R encoder mismatch

# === Kinect ===
KINECT_WARMUP_MINUTES = 10
KINECT_INVALID_DEPTH = [0, 2047]    # mask these out
```

---

*Document created: 2026-01-01*
*Last updated: 2026-01-01*
*Revision 3: Implemented depth conversion fix in frame_processor.py, updated pointcloud_widget for meters*
