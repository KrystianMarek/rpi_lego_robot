"""
PointCloudWidget - 3D visualization of Kinect depth data.

Uses pyqtgraph's OpenGL widget for real-time point cloud rendering.
"""
import numpy as np

try:
    import pyqtgraph.opengl as gl
    from pyqtgraph.opengl import GLViewWidget
    from PyQt5.QtGui import QVector3D
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False
    GLViewWidget = object  # Fallback for type hints
    QVector3D = None

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


class PointCloudWidget(QWidget):
    """
    Widget for displaying 3D point clouds from Kinect depth data.

    Falls back to a placeholder label if pyqtgraph is not installed.
    """

    # Subsample factor (stride=2 means every 2nd pixel → 1/4 points)
    SUBSAMPLE_STRIDE = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        if PYQTGRAPH_AVAILABLE:
            self._setup_gl_widget()
            self._setup_controls()
        else:
            self._setup_fallback()

    def _setup_gl_widget(self):
        """Setup OpenGL 3D view."""
        self._gl_widget = gl.GLViewWidget()

        # Initial camera - top-down angled view per user preference
        self._default_distance = 1500
        self._default_elevation = 90
        self._default_azimuth = -90
        self._default_center = QVector3D(0, 0, 600)

        # Apply initial camera position
        self._apply_camera_defaults()

        # Add small reference grid
        grid = gl.GLGridItem()
        grid.setSize(2000, 2000)
        grid.setSpacing(250, 250)
        grid.setColor((100, 100, 100, 80))  # Subtle gray
        self._gl_widget.addItem(grid)

        # Add small coordinate axes in corner
        self._add_axes()

        # Scatter plot for point cloud (created on first update)
        self._scatter = None

        # Add GL widget with stretch factor 1 (takes all available space)
        self._layout.addWidget(self._gl_widget, stretch=1)

    def _add_axes(self):
        """Add small XYZ coordinate axes away from data."""
        # Position axes in corner, away from typical point cloud data
        origin_offset = (-900, -700, -100)
        axis_length = 150
        axis_width = 2

        ox, oy, oz = origin_offset

        # X axis - Red
        x_axis = gl.GLLinePlotItem(
            pos=np.array([[ox, oy, oz], [ox + axis_length, oy, oz]]),
            color=(1, 0.3, 0.3, 1),
            width=axis_width,
            antialias=True
        )
        self._gl_widget.addItem(x_axis)

        # Y axis - Green
        y_axis = gl.GLLinePlotItem(
            pos=np.array([[ox, oy, oz], [ox, oy + axis_length, oz]]),
            color=(0.3, 1, 0.3, 1),
            width=axis_width,
            antialias=True
        )
        self._gl_widget.addItem(y_axis)

        # Z axis - Blue (depth direction)
        z_axis = gl.GLLinePlotItem(
            pos=np.array([[ox, oy, oz], [ox, oy, oz + axis_length]]),
            color=(0.3, 0.6, 1, 1),
            width=axis_width,
            antialias=True
        )
        self._gl_widget.addItem(z_axis)

        # Small endpoint markers
        endpoints = gl.GLScatterPlotItem(
            pos=np.array([
                [ox + axis_length, oy, oz],           # X end (red)
                [ox, oy + axis_length, oz],           # Y end (green)
                [ox, oy, oz + axis_length],           # Z end (blue)
            ]),
            color=np.array([
                [1, 0.3, 0.3, 1],
                [0.3, 1, 0.3, 1],
                [0.3, 0.6, 1, 1],
            ]),
            size=6
        )
        self._gl_widget.addItem(endpoints)

    def _setup_controls(self):
        """Setup compact control buttons."""
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 2, 5, 5)
        controls_layout.setSpacing(6)

        # Button style - readable
        btn_style = "QPushButton { padding: 4px 10px; font-size: 12px; }"

        for name, callback in [("⟲", self.reset_camera),
                                ("Front", self._set_front_view),
                                ("Top", self._set_top_view),
                                ("Side", self._set_side_view)]:
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            btn.setStyleSheet(btn_style)
            btn.setFixedHeight(26)
            controls_layout.addWidget(btn)

        # Axis legend
        legend = QLabel("<font color='#ff6666'>X</font> <font color='#66ff66'>Y</font> <font color='#6699ff'>Z</font>")
        legend.setStyleSheet("font-size: 12px; padding-left: 12px;")
        controls_layout.addWidget(legend)

        controls_layout.addStretch()

        # Camera angle display
        self._angle_label = QLabel()
        self._angle_label.setStyleSheet("font-size: 11px; color: #aaa;")
        controls_layout.addWidget(self._angle_label)
        self._update_angle_display()

        # Timer to update angles during mouse interaction
        self._angle_timer = QTimer(self)
        self._angle_timer.timeout.connect(self._update_angle_display)
        self._angle_timer.start(100)  # Update every 100ms

        # Add controls with stretch=0 (minimal space)
        self._layout.addLayout(controls_layout, stretch=0)

    def _update_angle_display(self):
        """Update the camera angle display."""
        if self._gl_widget and hasattr(self, '_angle_label'):
            elev = self._gl_widget.opts.get('elevation', 0)
            azim = self._gl_widget.opts.get('azimuth', 0)
            dist = self._gl_widget.opts.get('distance', 0)
            self._angle_label.setText(f"El:{elev:.0f}° Az:{azim:.0f}° D:{dist:.0f}")

    def _apply_camera_defaults(self):
        """Apply default camera settings."""
        self._gl_widget.opts['distance'] = self._default_distance
        self._gl_widget.opts['elevation'] = self._default_elevation
        self._gl_widget.opts['azimuth'] = self._default_azimuth
        self._gl_widget.opts['center'] = self._default_center
        self._update_angle_display()

    def _set_top_view(self):
        """Set camera to top-down view (looking down Z axis)."""
        if self._gl_widget:
            self._gl_widget.opts['distance'] = 3000
            self._gl_widget.opts['elevation'] = 90  # Directly above
            self._gl_widget.opts['azimuth'] = 0
            self._gl_widget.opts['center'] = QVector3D(0, 0, 600)
            self._update_angle_display()

    def _set_side_view(self):
        """Set camera to side view (looking along X axis)."""
        if self._gl_widget:
            self._gl_widget.opts['distance'] = 3000
            self._gl_widget.opts['elevation'] = 0   # Level
            self._gl_widget.opts['azimuth'] = 0     # Looking along X
            self._gl_widget.opts['center'] = QVector3D(0, 0, 600)
            self._update_angle_display()

    def _set_front_view(self):
        """Set camera to front view (robot's perspective, looking along Z)."""
        if self._gl_widget:
            self._gl_widget.opts['distance'] = 2500
            self._gl_widget.opts['elevation'] = 15
            self._gl_widget.opts['azimuth'] = 180   # Looking along +Z
            self._gl_widget.opts['center'] = QVector3D(0, 0, 800)
            self._update_angle_display()

    def _setup_fallback(self):
        """Setup fallback placeholder when pyqtgraph not available."""
        label = QLabel("Point Cloud requires pyqtgraph.\nInstall: pip install pyqtgraph PyOpenGL")
        label.setStyleSheet("color: #888; padding: 20px;")
        self._layout.addWidget(label)
        self._gl_widget = None
        self._scatter = None

    def update_pointcloud(self, points: np.ndarray, colors: np.ndarray = None):
        """
        Update the point cloud display.

        Args:
            points: (N, 3) array of XYZ coordinates
            colors: (N, 3) or (N, 4) array of RGB(A) colors (0-255)
                    If None, uses depth-based coloring
        """
        if not PYQTGRAPH_AVAILABLE or self._gl_widget is None:
            return

        if len(points) == 0:
            if self._scatter is not None:
                self._scatter.setData(pos=np.zeros((0, 3)))
            return

        # Prepare colors
        if colors is None:
            # Depth-based coloring (blue=near, red=far)
            z_min, z_max = points[:, 2].min(), points[:, 2].max()
            z_normalized = (points[:, 2] - z_min) / (z_max - z_min + 1e-6)
            colors = np.zeros((len(points), 4), dtype=np.float32)
            colors[:, 0] = z_normalized        # Red increases with distance
            colors[:, 2] = 1.0 - z_normalized  # Blue decreases with distance
            colors[:, 3] = 1.0                 # Alpha
        else:
            # Convert colors to float32 [0-1] with alpha
            if colors.dtype == np.uint8:
                colors = colors.astype(np.float32) / 255.0

            if colors.shape[1] == 3:
                # Add alpha channel
                alpha = np.ones((len(colors), 1), dtype=np.float32)
                colors = np.hstack([colors, alpha])

        # Ensure float32 for OpenGL
        points = points.astype(np.float32)
        colors = colors.astype(np.float32)

        # Update or create scatter plot
        if self._scatter is None:
            self._scatter = gl.GLScatterPlotItem(
                pos=points,
                color=colors,
                size=2,
                pxMode=True  # Size in pixels
            )
            self._gl_widget.addItem(self._scatter)
        else:
            self._scatter.setData(pos=points, color=colors)

    def clear(self):
        """Clear the point cloud display."""
        if self._scatter is not None:
            self._scatter.setData(pos=np.zeros((0, 3)))

    def set_camera_distance(self, distance: float):
        """Set camera distance from origin."""
        if self._gl_widget:
            self._gl_widget.opts['distance'] = distance

    def reset_camera(self):
        """Reset camera to default position (matching video perspective)."""
        if self._gl_widget:
            self._apply_camera_defaults()

