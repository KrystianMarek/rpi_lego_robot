# Guidance Request: 3D Scene Reconstruction for LEGO Robot

## Purpose of This Document

We are developing a **3D scene reconstruction feature** for an existing robotics project and seek expert guidance on areas where our confidence is low. This document provides complete context for review.

**What we're asking for:**
1. Review of our proposed implementation plan
2. Guidance on specific technical challenges (listed below)
3. Identification of potential issues we may have overlooked
4. Recommendations for libraries, algorithms, or approaches

---

## Project Overview

### The Robot: K.O.C (Kinect on Caterpillar)

A remote-controlled LEGO robot with:
- **Caterpillar tracks** for differential drive (tank steering)
- **Rotating turret** with mounted Xbox 360 Kinect sensor
- **Raspberry Pi 3** running the server (motor control, sensor reading, Kinect capture)
- **PC client** with PyQt5 GUI for remote control and visualization

**Repository**: https://github.com/KrystianMarek/rpi_lego_robot/tree/main

### Physical Configuration

```
                    ┌─────────────────┐
                    │  Xbox 360 Kinect │  ← Mounted HIGH on turret (~15-20cm above body)
                    │  (RGB + Depth)   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │     Turret      │  ← Rotates independently via geared motor
                    │  (LEGO Technic) │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │    Lazy Susan Rotation Platform  │
            └────────────────┬────────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │              Main Robot Body                     │
    │  ┌─────────┐                      ┌─────────┐   │
    │  │ BrickPi │                      │Ultrasonic│   │  ← Fixed to body (front-facing)
    │  │ (blue)  │                      │ Sensor   │   │     Does NOT rotate with turret
    │  └─────────┘                      └─────────┘   │
    │           LEGO Technic Frame + Raspberry Pi     │
    └────────────────────────┬────────────────────────┘
                             │
    ┌────────────────────────┴────────────────────────┐
    │              Caterpillar Tracks                  │
    │     Left Motor ◄──────────────────► Right Motor │
    └─────────────────────────────────────────────────┘
```

**Robot Photos**: Available in repository at `pictures/pic1.jpg` and `pictures/pic2.jpg`

### Current Tech Stack

| Component | Technology |
|-----------|------------|
| Server (RPi) | Python 3, libfreenect, BrickPi library |
| Client (PC) | Python 3, PyQt5, pyqtgraph (OpenGL) |
| Networking | ZeroMQ (PUB/SUB for telemetry, PUSH/PULL for commands) |
| Point Cloud | pyqtgraph.opengl.GLScatterPlotItem |
| Serialization | pickle + lz4 compression |

### What Already Works

1. **Real-time video streaming** - RGB (640×480) from Kinect to GUI
2. **Real-time depth streaming** - 11-bit depth (640×480) with colormap display
3. **Point cloud visualization** - Depth converted to XYZ points, rendered in OpenGL tab
4. **Telemetry** - Motor encoders, temperature, voltage, ultrasonic sensor
5. **Robot control** - Movement commands (forward, backward, turn) and turret rotation
6. **Turret encoder** - Tracking turret rotation angle (raw encoder values)

### Current Point Cloud Pipeline

```python
# Server side (kinect_process.py)
video_frame = freenect.sync_get_video()      # 640×480 RGB
depth_array = freenect.sync_get_depth()       # 640×480, 11-bit raw depth
# Sent as KinectPacket via ZMQ

# Client side (frame_processor.py)
def depth_to_colored_pointcloud(depth_array, video_frame):
    # Using default Kinect v1 intrinsics
    fx, fy = 594.21, 591.04  # Focal lengths (pixels)
    cx, cy = 339.5, 242.7    # Principal point (pixels)

    # Filter invalid depth (Config values)
    valid_mask = (z > 300) & (z < 1800)  # Raw depth units

    # Project to 3D
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    # z remains as raw depth value (NOT converted to real units)

    return points, colors  # Displayed in PointCloudWidget
```

---

## The Feature We Want to Build

### Goal

Create a **3D reconstruction of the scene** by:
1. Detecting objects in the video stream (toys, furniture, etc.)
2. Extracting point cloud segments for each detected object
3. Tracking robot/turret pose to transform points to world coordinates
4. Merging observations from multiple viewpoints as robot/turret moves
5. Displaying the accumulated scene in a dedicated GUI tab

### Expected User Flow

1. User clicks "Start Scan" in new GUI tab
2. User rotates turret and/or drives robot to capture different viewpoints
3. System detects objects, segments their point clouds, registers to world frame
4. Accumulated 3D scene updates in real-time
5. User can export the reconstructed scene

### Proposed Implementation Plan

Full plan: `doc/development/todo-3d-scene-reconstruction.md` in repository

**Phases:**
- Phase 0: Calibration (encoder ratios, Kinect depth validation)
- Phase 1: Object Detection (YOLO/MobileNet integration)
- Phase 2: Pose Estimation (encoder-based odometry)
- Phase 3: Point Cloud Segmentation (extract object points)
- Phase 4: Multi-view Registration (ICP alignment)
- Phase 5: Scene Management (object tracking, merging)
- Phase 6: 3D Viewer Widget (render accumulated scene)

---

## Confidence Assessment

### High Confidence ✅

| Area | Reason |
|------|--------|
| Object Detection (Phase 1) | YOLO/ultralytics well-documented, many examples |
| GUI Integration (Phase 6) | Already have working OpenGL point cloud widget |
| Data Structures | Python dataclasses, straightforward design |
| ZMQ Networking | Already working, just need to extend |

### Medium Confidence ⚠️

| Area | Concern |
|------|---------|
| Point Cloud Segmentation (Phase 3) | Projecting bbox back to 3D, depth discontinuities at object edges |
| Scene Management (Phase 5) | Object tracking when turret rotates (objects move in image but not in world) |
| Performance | Running detection + registration at ~2 FPS may be challenging |

### Low Confidence ❓ (Need Guidance)

| Area | Specific Questions |
|------|-------------------|
| **Kinect Depth Calibration** | See Section A below |
| **Encoder-Based Odometry** | See Section B below |
| **Point Cloud Registration** | See Section C below |
| **Coordinate Transforms** | See Section D below |

---

## Areas Requiring Guidance

### A. Kinect v1 Depth Calibration

**Context**: Xbox 360 Kinect outputs 11-bit "raw depth" values (0-2047). These are NOT millimeters.

**Current code** treats raw values directly as Z coordinate (no conversion):
```python
z = depth_array.astype(np.float32)  # Raw 11-bit value used as-is
x = (u - cx) * z / fx
y = (v - cy) * z / fy
```

**Our calibration plan**: Place objects at known distances (10cm, 20cm, 50cm, 100cm), record raw depth values, compute conversion.

**Questions:**
1. Is Kinect v1 depth-to-distance conversion **linear** (simple scale+offset) or **non-linear** (polynomial/lookup table needed)?
2. Are the default intrinsic parameters (fx=594.21, fy=591.04, cx=339.5, cy=242.7) reliable, or should we calibrate these too?
3. What's the typical accuracy we can expect from Kinect v1 at different distances?
4. Should we account for **temperature drift** or **warm-up time** affecting depth accuracy?

**Reference**: We found various formulas online but they differ:
- Some use: `distance_mm = 1.0 / (raw_depth * -0.0030711016 + 3.3309495161)`
- Others suggest raw depth IS proportional to 1/distance (disparity)

---

### B. Encoder-Based Odometry with Geared Motors

**Context**: All motors use LEGO Technic **gear reductions**. Raw encoder values ≠ actual rotation.

**Available data**:
- Left motor encoder (angle in degrees, but through unknown gear ratio)
- Right motor encoder (same)
- Turret motor encoder (same)

**Calibration plan**:
- Drive robot exactly 1 meter, record encoder delta → compute ticks/mm
- Rotate turret 90°, record encoder delta → compute ticks/degree

**Questions:**
1. Is simple **dead reckoning** (integrate encoder deltas) sufficient for short scanning sessions (~5 minutes)?
2. How significant is **wheel slip** on caterpillar tracks vs wheeled robots?
3. Should we implement **slip detection** (compare left vs right encoder for straight-line travel)?
4. For turret rotation, is encoder-based angle reliable, or do we need **homing** (reset to known position)?
5. Any recommendations for **drift correction** without external sensors (no IMU, no GPS)?

**Concern**: Accumulated error over time will cause point cloud misalignment.

---

### C. Point Cloud Registration (ICP)

**Context**: Need to align point clouds from different turret angles / robot positions.

**Planned approach**:
1. Transform each observation to world frame using pose estimate
2. Use ICP to refine alignment when merging with existing object cloud
3. Use Open3D library

**Questions:**
1. Given our depth resolution and noise, what **ICP threshold** (max correspondence distance) should we start with?
2. Should we use **point-to-point** or **point-to-plane** ICP? (We won't have normals initially)
3. How do we detect **ICP failure** (converged to wrong local minimum)?
4. For objects seen from very different angles (e.g., front vs back), will ICP work or do we need **global registration** first?
5. Is **Colored ICP** worth the extra complexity given Kinect's RGB/depth offset?
6. Should we downsample point clouds before ICP? What voxel size relative to expected object size?

**Concern**: ICP is notoriously sensitive to initialization. Our pose estimate may not be accurate enough.

---

### D. Coordinate System Transforms

**Our planned coordinate system**:
```
World Frame (Right-handed):
    Y (up)
    │
    │
    └────── X (right)
   /
  Z (forward - robot facing direction at start)
```

**Transform chain**:
```
Kinect Frame → Turret Frame → Robot Frame → World Frame
     │              │              │             │
     │              │              │             └── Robot translation/rotation from odometry
     │              │              └── Turret rotation angle
     │              └── Kinect mount offset (X, Y, Z) on turret
     └── Intrinsic projection (fx, fy, cx, cy)
```

**Questions:**
1. Is our transform chain order correct? Should it be world = T_robot × T_turret × T_kinect_mount × point_kinect?
2. The Kinect on this robot appears to have a **slight downward tilt** for floor visibility. How do we incorporate this? Additional rotation matrix?
3. For homogeneous transforms, should we work in mm or meters for numerical stability?
4. Any common pitfalls in robotics coordinate transforms we should watch for?

---

### E. Object Tracking Across Frames

**Context**: When turret rotates, detected objects move in the image but stay fixed in world space.

**Challenge**: Matching detections across frames when:
- Same object appears at different image locations (turret moved)
- Same object seen from different angles (partial view vs full view)
- Object temporarily occluded then reappears

**Planned approach**:
1. Transform detection centroid to world coordinates
2. Match by: same class + world centroid within threshold distance
3. If no match, create new object

**Questions:**
1. Is centroid-based matching sufficient, or do we need **appearance features** (color histogram, etc.)?
2. What distance threshold for "same object"? Depends on object size?
3. How to handle **object splitting** (one large detection becomes two smaller ones)?
4. Should we use established **multi-object tracking** (MOT) algorithms like SORT/DeepSORT, or is our simpler approach okay for static scenes?

---

### F. Segmentation Quality

**Context**: We want to extract the point cloud for each detected object using its 2D bounding box.

**Planned approach**:
1. For each pixel in bbox, check if it projects into the 3D frustum
2. Apply depth clustering (DBSCAN) to separate foreground from background
3. Take cluster closest to camera

**Questions:**
1. Kinect v1 has significant **depth shadow** artifacts at object edges. How do we handle this?
2. Is projecting bbox to 3D sufficient, or should we use the **depth discontinuity** to find object boundaries?
3. For objects at similar depths (e.g., object on table), how do we separate them?
4. Should we invest in **instance segmentation** (per-pixel mask) instead of bbox + clustering?

---

## Summary of Key Questions

| Priority | Question | Area |
|----------|----------|------|
| **Critical** | Is Kinect depth linear or need polynomial conversion? | Calibration |
| **Critical** | Will dead reckoning work for ~5 min sessions? | Odometry |
| **Critical** | What ICP parameters for noisy Kinect data? | Registration |
| **High** | Correct transform chain order? | Coordinates |
| **High** | How to handle depth shadows at edges? | Segmentation |
| **Medium** | Simple centroid matching vs MOT algorithm? | Tracking |
| **Medium** | Point-to-point vs point-to-plane ICP? | Registration |

---

## Constraints

- **No IMU** - Cannot add inertial measurement unit
- **No external tracking** - No motion capture, fiducial markers, etc.
- **Client-side processing** - All reconstruction happens on PC, not RPi
- **Real-time-ish** - Aim for updates every few seconds, not every frame
- **Indoor environment** - Known lighting, static scene (objects don't move during scan)

---

## Relevant Files in Repository

| File | Purpose |
|------|---------|
| `app/client/frame_processor.py` | Current depth→pointcloud conversion |
| `app/client/pointcloud_widget.py` | Current OpenGL visualization |
| `app/common/config.py` | Kinect intrinsics and depth thresholds |
| `app/server/kinect_process.py` | Server-side Kinect capture |
| `app/networking/packets.py` | Data packet definitions |
| `doc/development/todo-3d-scene-reconstruction.md` | Full implementation plan |
| `pictures/pic1.jpg`, `pic2.jpg` | Robot physical photos |

---

## What We're Looking For

1. **Validation** - Is our overall approach sound?
2. **Corrections** - Have we misunderstood anything fundamental?
3. **Recommendations** - Better algorithms, libraries, or approaches?
4. **Warnings** - Pitfalls or failure modes we haven't considered?
5. **Parameter Suggestions** - Starting values for thresholds, etc.

Thank you for your guidance!

---

*Document created: 2026-01-01*
*Project: K.O.C (Kinect on Caterpillar)*
*Repository: https://github.com/KrystianMarek/rpi_lego_robot*

