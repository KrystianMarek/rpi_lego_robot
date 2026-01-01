# GUI Layout Refactoring TODO

## Analysis Summary

**Date:** 2026-01-01
**Files Analyzed:**
- `gui.py` - Entry point
- `app/client/gui/main_window.py` - Auto-generated UI code
- `app/client/gui/main_window.ui` - Qt Designer file
- `app/client/gui/MainWindowWrapper.py` - Controller logic

### Goals

1. **Primary:** Fix layout issues (non-responsive, uneven sections, poor organization)
2. **Parallel:** Streamline and clean up messy existing code
   - The auto-generated `main_window.py` is hard to maintain
   - Widget naming is inconsistent and non-descriptive
   - Logic is scattered (video options, status bar, telemetry)
   - This refactor is an opportunity to improve code quality alongside UI/UX

---

## Current Problems

### 1. Fixed/Absolute Positioning - Not Responsive

The UI uses **absolute pixel positioning** throughout, causing sections to not scale with window resize:

```python
# main_window.py - Fixed geometry examples:
self.widget.setGeometry(QtCore.QRect(10, 10, 1291, 481))      # Video area
self.widget1.setGeometry(QtCore.QRect(10, 500, 1291, 391))    # Controls area
self.kinect_video.setGeometry(QtCore.QRect(0, 0, 640, 480))   # Fixed 640x480
self.label_10.setGeometry(QtCore.QRect(0, 0, 640, 480))       # Fixed 640x480
```

**Root cause:** Widgets are placed as children of container widgets (`widget`, `widget1`) with fixed geometry, instead of being managed by a proper central layout.

### 2. Uneven Control Section Distribution

Current control sections are not evenly spaced:
- `locomotion` and `turret_controls` are grouped in `locomotion_and_controls` layout
- `video_options` and `sensors` (groupBox_2) are grouped in `other_sensors_and_controlls` layout
- This creates uneven visual distribution

### 3. Nested Section Confusion

The **Connection** groupbox (`groupBox_3`) is nested **inside** `video_options`, making the structure illogical:

```xml
<!-- main_window.ui structure -->
<widget class="QGroupBox" name="video_options">
  ...
  <widget class="QGroupBox" name="groupBox_3">  <!-- Connection nested here! -->
    <property name="title"><string>Connection</string></property>
    ...
  </widget>
</widget>
```

### 4. Telemetry Split Across Status Bar and Sensors Section

Telemetry data is scattered in two places:

**Status bar:**
```python
# MainWindowWrapper.py
self._stats_label = QLabel("CPU: --% | RAM: --% | WiFi: -- Mbps")
self._frames_label = QLabel("Video: -- fps | Depth: -- fps")
```

**Sensors section:** Temperature, Voltage, Ultrasound

**Solution:** Consolidate all telemetry in one "Telemetry" section and remove the status bar entirely.

### 5. Poor Widget Naming

Non-descriptive names make maintenance difficult:
- `label_10` → should be `kinect_depth` or `depth_label`
- `groupBox_2` → should be `sensors_group` / `telemetry_group`
- `groupBox_3` → should be `connection_group`
- `widget`, `widget1`, `widget2` → generic container names

### 6. Point Cloud Opens as Separate Window

The point cloud view opens as a **separate popup window** rather than being integrated:

```python
# MainWindowWrapper.py
self._pointcloud_widget = PointCloudWidget()
self._pointcloud_widget.hide()
# ...
def _on_video_mode_changed(self):
    if self._main_window.radioButton_cloud_point.isChecked():
        self._pointcloud_widget.show()  # Opens separate window!
    else:
        self._pointcloud_widget.hide()
```

This is disjointed UX - the point cloud should be in the main window alongside video streams.

---

## Proposed Architecture

### Target Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ MainWindow                                                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Central Widget (QVBoxLayout)                                    │ │
│ │ ┌─────────────────────────────────────────────────────────────┐ │ │
│ │ │ QTabWidget (stretch: 3)                                     │ │ │
│ │ │ ┌─────────────────────────────────────────────────────────┐ │ │ │
│ │ │ │ [📹 Streams] [🔲 Point Cloud]                  <- tabs  │ │ │ │
│ │ │ ├─────────────────────────────────────────────────────────┤ │ │ │
│ │ │ │ Tab 1: Streams                                          │ │ │ │
│ │ │ │  ┌─────────────────┐ ┌─────────────────┐                │ │ │ │
│ │ │ │  │  Video Stream   │ │  Depth Stream   │                │ │ │ │
│ │ │ │  │ (scalable)      │ │ (scalable)      │                │ │ │ │
│ │ │ │  └─────────────────┘ └─────────────────┘                │ │ │ │
│ │ │ ├─────────────────────────────────────────────────────────┤ │ │ │
│ │ │ │ Tab 2: Point Cloud                                      │ │ │ │
│ │ │ │  ┌─────────────────────────────────────────────────────┐│ │ │ │
│ │ │ │  │  PointCloudWidget (GLViewWidget)                    ││ │ │ │
│ │ │ │  │  - 3D interactive view                              ││ │ │ │
│ │ │ │  │  - Camera controls (Reset, Front, Top, Side)        ││ │ │ │
│ │ │ │  └─────────────────────────────────────────────────────┘│ │ │ │
│ │ │ └─────────────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────────────┐ │ │
│ │ │ Controls Area (QHBoxLayout) - stretch: 1                    │ │ │
│ │ │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│ │ │
│ │ │  │Locomotion│ │  Turret  │ │Connection│ │    Telemetry     ││ │ │
│ │ │  │          │ │          │ │          │ │                  ││ │ │
│ │ │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│ │ │
│ │ └─────────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
(Status bar removed - all telemetry consolidated in Telemetry section)
```

### Tabbed Video Area Design

**QTabWidget** replaces the fixed video container:

| Tab | Name | Contents |
|-----|------|----------|
| 1 | **Streams** | Video + Depth side-by-side (QHBoxLayout with two QLabels) |
| 2 | **Point Cloud** | Embedded `PointCloudWidget` (3D GLViewWidget) |

**Benefits:**
- Point cloud is integrated into main window (no separate popup)
- Cleaner UI - tabs naturally replace "video options" radio buttons
- Users switch views by clicking tabs instead of radio buttons
- Point cloud widget gets full video area space when selected

**Implementation notes:**
- `PointCloudWidget` already exists at `app/client/pointcloud_widget.py`
- Currently shown via `self._pointcloud_widget.show()` as separate window
- Will be embedded as Tab 2 content instead
- Remove `radioButton_video`, `radioButton_depth`, `radioButton_cloud_point`
- Remove `video_options` GroupBox entirely (tabs replace its function)

### Section Reorganization

| Current Section | New Section | Changes |
|-----------------|-------------|---------|
| `locomotion` | **Locomotion** | Keep as-is |
| `turret_controls` | **Turret** | Keep as-is |
| `video_options` | ~~REMOVED~~ | Replaced by QTabWidget tabs |
| `groupBox_3` (nested) | **Connection** | Extract as standalone top-level section |
| `groupBox_2` (sensors) | **Telemetry** | Rename; add CPU/RAM/WiFi/FPS displays |

**Result:** 4 control sections (down from 5) + tabbed video area

### Telemetry Section Contents (Consolidated)

**All telemetry in one place** - status bar removed entirely:

| Category | Metrics |
|----------|---------|
| **System** | CPU %, RAM % (MB), WiFi bandwidth (Mbps) |
| **Streams** | Video FPS, Depth FPS |
| **Sensors** | Temperature, Voltage, Ultrasound |
| **Motors** | *(already in Locomotion/Turret sections)* |

This eliminates the status bar and provides a cleaner, more organized display.

---

## TODO Tasks

### Phase 1: Layout Infrastructure

- [x] **1.1** Replace fixed widget containers with proper main layout ✅
  - Remove `widget` and `widget1` fixed-geometry containers
  - Add `QVBoxLayout` to `centralwidget`
  - Use stretch factors for video/controls ratio (3:1)

- [x] **1.2** Create QTabWidget for video area ✅
  - Create `QTabWidget` as main video container
  - Tab 1 "📹 Streams": Contains video + depth side-by-side
  - Tab 2 "🔲 Point Cloud": Contains embedded `PointCloudWidget`
  - Set `QSizePolicy.Expanding` on tab widget

- [x] **1.3** Make video streams responsive ✅
  - Remove fixed 640x480 geometry from video labels
  - Set `QSizePolicy.Expanding` on video stream labels
  - Use `QHBoxLayout` with stretch for Tab 1 content
  - Using `setScaledContents(True)` for simplicity

- [x] **1.4** Embed PointCloudWidget in Tab 2 ✅
  - Move `PointCloudWidget` from separate window to Tab 2
  - Remove `self._pointcloud_widget.show()` calls
  - Remove `self._pointcloud_widget.hide()` calls
  - Widget embedded via `pointcloud_layout.addWidget()`

- [x] **1.5** Create proper controls layout ✅
  - Use `QHBoxLayout` with equal stretch for all 4 sections
  - Set minimum sizes on group boxes to prevent collapsing

### Phase 2: Section Reorganization

- [x] **2.1** Remove Video Options section entirely ✅
  - Delete `video_options` GroupBox
  - Delete radio buttons (`radioButton_video`, `radioButton_depth`, `radioButton_cloud_point`)
  - Tabs now provide view switching functionality
  - Remove `_setup_video_options()` method from MainWindowWrapper
  - Remove `_on_video_mode_changed()` method from MainWindowWrapper

- [x] **2.2** Extract Connection as standalone section ✅
  - Create standalone `connection_group` GroupBox
  - Move from nested inside video_options to controls row
  - Contains: IP input, connect button, progress bar

- [x] **2.3** Rename Sensors to Telemetry ✅
  - Rename `groupBox_2` → `telemetry_group`
  - Update title from "sensors" to "Telemetry"

- [x] **2.4** Consolidate ALL telemetry in Telemetry section ✅
  - Add LCD/labels for: CPU %, RAM %, WiFi Mbps
  - Add LCD/labels for: Video FPS, Depth FPS
  - Keep existing: Temperature, Voltage, Ultrasound
  - Using 2-column grid layout for compact display
  - Status bar removed

### Phase 3: Widget Naming Cleanup

- [x] **3.1** Rename video/depth displays ✅
  - `kinect_video` → keep (good name)
  - `label_10` → `kinect_depth`

- [x] **3.2** Rename group boxes ✅
  - `groupBox_2` → `telemetry_group`
  - `groupBox_3` → `connection_group`

- [x] **3.3** Name new tab widget ✅
  - Add `video_tab_widget` for the QTabWidget

### Phase 4: Update MainWindowWrapper

- [x] **4.1** Remove/simplify video mode handling ✅
  - Remove `_setup_video_options()` method
  - Remove `_on_video_mode_changed()` method
  - Remove radio button signal connections

- [x] **4.2** Add tab change handling ✅
  - Connect to `QTabWidget.currentChanged` signal
  - Only update point cloud when Tab 2 is visible (performance)
  - Always update video/depth streams

- [x] **4.3** Update Kinect data handling ✅
  - In `update_kinect()`: always update video/depth labels
  - In `update_kinect()`: only generate point cloud when Tab 2 active
  - Check `video_tab_widget.currentIndex()` for optimization

- [x] **4.4** Remove status bar entirely ✅
  - Remove `_setup_stats_display()` method
  - Remove `_stats_label` and `_frames_label`
  - No status bar in new layout
  - All data now displayed in Telemetry section

- [x] **4.5** Update telemetry display method ✅
  - Add new LCD updates for CPU/RAM/WiFi/FPS in telemetry section
  - Create new widget references for added displays
  - Update all `self._main_window.xxx` references

### Phase 5: Testing & Polish

- [x] **5.1** Test window resizing behavior ✅
- [x] **5.2** Test minimum window size constraints ✅
- [x] **5.3** Verify tab switching works correctly ✅
- [x] **5.4** Verify point cloud only updates when visible ✅
- [x] **5.5** Verify all telemetry updates work ✅
- [x] **5.6** Test keyboard shortcuts still work ✅

**Manual testing completed successfully on 2026-01-01.**

---

## Implementation Status

**Date Completed:** 2026-01-01

All phases 1-4 have been implemented. The GUI has been completely refactored:

### Files Modified
- `app/client/gui/main_window.py` - Complete rewrite with responsive layout
- `app/client/gui/MainWindowWrapper.py` - Updated to work with new UI structure

### Key Changes
1. Replaced fixed-geometry layout with proper `QVBoxLayout` + stretch factors
2. Added `QTabWidget` with "📹 Streams" and "🔲 Point Cloud" tabs
3. Point cloud now embedded in main window (no separate popup)
4. 4 evenly distributed control sections: Locomotion, Turret, Connection, Telemetry
5. All telemetry consolidated in Telemetry section (CPU, RAM, WiFi, FPS, Temp, Voltage, Ultrasound)
6. Status bar removed
7. Responsive video streams with `setScaledContents(True)`
8. Point cloud only updates when its tab is visible (performance optimization)

---

## Implementation Notes

### Approach Options

**Option A: Modify `.ui` file in Qt Designer**
- Pros: Visual editing, maintains `.ui` source file
- Cons: Requires Qt Designer, regenerate `main_window.py`

**Option B: Modify `main_window.py` directly**
- Pros: Direct code control, no tools needed
- Cons: File header says "All changes will be lost" - need to either:
  - Stop regenerating from `.ui`
  - OR update `.ui` and regenerate

**Option C: Build layout programmatically in MainWindowWrapper**
- Pros: Full Python control, no `.ui` dependency
- Cons: More code in wrapper, mixes layout with logic

**Recommended:** Option B - modify `main_window.py` directly and deprecate `.ui` file.
The changes are significant enough that Qt Designer may be cumbersome.

### QTabWidget Setup

```python
from PyQt5.QtWidgets import QTabWidget

# Create tab widget
self.video_tab_widget = QTabWidget(self.centralwidget)

# Tab 1: Streams (video + depth)
streams_widget = QWidget()
streams_layout = QHBoxLayout(streams_widget)
streams_layout.addWidget(self.kinect_video, stretch=1)
streams_layout.addWidget(self.kinect_depth, stretch=1)
self.video_tab_widget.addTab(streams_widget, "📹 Streams")

# Tab 2: Point Cloud
self.pointcloud_widget = PointCloudWidget()
self.video_tab_widget.addTab(self.pointcloud_widget, "🔲 Point Cloud")

# Add to main layout with stretch
main_layout.addWidget(self.video_tab_widget, stretch=3)
```

### Size Policy Reference

For responsive layouts, use these size policies:
```python
from PyQt5.QtWidgets import QSizePolicy

# Tab widget - expand in both directions
self.video_tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

# Video labels - expand to fill available space
self.kinect_video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
self.kinect_depth.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

# Control sections - expand horizontally, preferred vertically
group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

# Stretch factors in layouts
main_layout.addWidget(self.video_tab_widget, stretch=3)  # 3x space for video
main_layout.addWidget(controls_area, stretch=1)          # 1x space for controls
```

### Point Cloud Tab Optimization

Only update point cloud when Tab 2 is visible to save CPU/GPU:

```python
def update_kinect(self, data: KinectPacket):
    # Always update video/depth displays
    self._main_window.kinect_video.setPixmap(...)
    self._main_window.kinect_depth.setPixmap(...)

    # Only update point cloud if tab is visible
    if self._main_window.video_tab_widget.currentIndex() == 1:
        points, colors = FrameProcessor.depth_to_colored_pointcloud(...)
        self._pointcloud_widget.update_pointcloud(points, colors)
```

### Video Scaling Considerations

Option 1: `setScaledContents(True)` - simple but may distort aspect ratio
Option 2: Custom resize event with aspect ratio preservation
Option 3: Use `QGraphicsView` for advanced scaling

**Recommended:** Start with `setScaledContents(True)` for simplicity.
Kinect streams are 640x480 (4:3) - distortion is minimal in most window sizes.

---

## Priority Order

1. **High:** Phase 1.1-1.2 (Main layout + QTabWidget) - core architecture
2. **High:** Phase 1.3-1.4 (Responsive streams + embedded point cloud) - core feature
3. **High:** Phase 2.1-2.2 (Remove video options, extract connection) - cleanup
4. **Medium:** Phase 2.3-2.4 (Telemetry section) - user requested
5. **Medium:** Phase 4 (MainWindowWrapper updates) - necessary for functionality
6. **Low:** Phase 3, 5 (Naming cleanup, testing) - polish

---

## References

- Current UI screenshot shows the fixed layout issues
- PyQt5 Layout Management: https://doc.qt.io/qt-5/layout.html
- QTabWidget: https://doc.qt.io/qt-5/qtabwidget.html
- PointCloudWidget: `app/client/pointcloud_widget.py` (pyqtgraph GLViewWidget)

