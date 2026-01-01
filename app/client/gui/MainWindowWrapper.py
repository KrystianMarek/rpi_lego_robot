"""
MainWindowWrapper - PyQt5 GUI for controlling the robot.

This is the main controller that connects the UI (main_window.py) with
the networking layer (ConnectionManager) and handles all user interactions.
"""
import logging
import time

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QDialog

from app.client.connection_manager import ConnectionManager, ConnectionState
from app.client.frame_processor import FrameProcessor
from app.client.pointcloud_widget import PointCloudWidget
from app.client.gui.main_window import Ui_MainWindow
from app.networking import (
    CommandPacket, TurnLeft, TurnRight, TurretLeft, TurretRight,
    GoForward, GoBackward, GoLeft, GoRight, TurretReset,
    KinectPacket, TelemetryPacket
)


class MainWindowWrapper(QDialog):
    """
    Main window controller that connects UI with networking.

    Handles:
    - Connection management (connect/disconnect)
    - Telemetry display updates
    - Kinect frame display (video, depth, point cloud)
    - Command button handling
    """

    command_packet_signal = pyqtSignal(CommandPacket)

    # Tab indices
    TAB_STREAMS = 0
    TAB_POINTCLOUD = 1

    def __init__(self, app, main_window: QMainWindow, default_robot_ip: str = ''):
        QDialog.__init__(self)
        self._logger = logging.getLogger(__name__)
        self._main_window = Ui_MainWindow()
        self._main_window.setupUi(main_window)
        self._main_window_ref = main_window
        self._app = app

        # FPS tracking
        self._video_frame_count = 0
        self._depth_frame_count = 0
        self._telemetry_count = 0
        self._last_fps_time = time.time()
        self._video_fps = 0.0
        self._depth_fps = 0.0
        self._fps_update_interval = 1.0  # Update FPS every second

        # Connection manager handles all networking
        self._connection_manager = ConnectionManager()
        self._connection_manager.state_changed.connect(self._on_connection_state_changed)
        self._connection_manager.error_occurred.connect(self._on_connection_error)
        self._connection_manager.telemetry_received.connect(self.update_telemetry)
        self._connection_manager.kinect_received.connect(self.update_kinect)

        # Set default robot IP from environment if provided
        if default_robot_ip:
            self._main_window.robot_ip_address.setText(default_robot_ip)
            self._logger.info("Robot IP loaded from environment: {}".format(default_robot_ip))

        # Embed PointCloudWidget in Tab 2
        self._pointcloud_widget = PointCloudWidget()
        self._main_window.pointcloud_layout.addWidget(self._pointcloud_widget)

        # Store last kinect data for point cloud generation
        self._last_video_frame = None
        self._last_depth_array = None

        # Setup UI connections
        self._setup_buttons()
        self._setup_tab_handling()

        # Handle window close
        self._main_window_ref.closeEvent = self._on_window_close

    def _on_window_close(self, event):
        """Handle window close event."""
        self._logger.info("Window closing, cleaning up...")
        self.cleanup()
        event.accept()

    def cleanup(self):
        """Disconnect and cleanup resources."""
        self._logger.info("Cleanup: disconnecting from robot...")

        # Disconnect from robot
        if self._connection_manager.is_connected:
            self._connection_manager.disconnect()

        self._logger.info("Cleanup complete.")

    def _setup_tab_handling(self):
        """Setup tab change handling for point cloud optimization."""
        self._main_window.video_tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int):
        """Handle tab changes - used for point cloud optimization."""
        if index == self.TAB_POINTCLOUD:
            self._logger.debug("Switched to Point Cloud tab")
            # If we have cached data, update point cloud immediately
            if self._last_depth_array is not None and self._last_video_frame is not None:
                try:
                    points, colors = FrameProcessor.depth_to_colored_pointcloud(
                        self._last_depth_array, self._last_video_frame)
                    self._pointcloud_widget.update_pointcloud(points, colors)
                except Exception as e:
                    self._logger.warning(f"Point cloud error: {e}")

    def on_connect_button(self):
        """Handle connect/disconnect button click."""
        if self._connection_manager.is_connected:
            # Disconnect
            self._connection_manager.disconnect()
        else:
            # Connect
            ip_address = self._main_window.robot_ip_address.text()
            self._logger.info("Connecting to {}".format(ip_address))
            self._connection_manager.connect(ip_address)

    def _on_connection_state_changed(self, state: ConnectionState):
        """Update UI based on connection state."""
        if state == ConnectionState.CONNECTED:
            self._main_window.connect_to_robot.setText("Disconnect")
            self._main_window.connect_to_robot.setEnabled(True)
            self._main_window.robot_ip_address.setEnabled(False)
            self._main_window.robot_ip_address.clearFocus()
        elif state == ConnectionState.DISCONNECTED:
            self._main_window.connect_to_robot.setText("Connect")
            self._main_window.connect_to_robot.setEnabled(True)
            self._main_window.robot_ip_address.setEnabled(True)
        elif state == ConnectionState.CONNECTING:
            self._main_window.connect_to_robot.setText("Connecting...")
            self._main_window.connect_to_robot.setEnabled(False)
        elif state == ConnectionState.ERROR:
            self._main_window.connect_to_robot.setText("Connect")
            self._main_window.connect_to_robot.setEnabled(True)
            self._main_window.robot_ip_address.setEnabled(True)

    def _on_connection_error(self, error_message: str):
        """Handle connection errors."""
        self._logger.error(f"Connection error: {error_message}")

    def update_kinect(self, data: KinectPacket):
        """Update video and depth displays from Kinect data."""
        self._logger.debug("Got kinect packet!")

        # Update frame counters and calculate FPS
        self._video_frame_count += 1
        self._depth_frame_count += 1

        current_time = time.time()
        elapsed = current_time - self._last_fps_time
        if elapsed >= self._fps_update_interval:
            self._video_fps = self._video_frame_count / elapsed
            self._depth_fps = self._depth_frame_count / elapsed
            self._video_frame_count = 0
            self._depth_frame_count = 0
            self._last_fps_time = current_time

            # Update FPS displays in telemetry section
            self._main_window.lcd_video_fps.display(self._video_fps)
            self._main_window.lcd_depth_fps.display(self._depth_fps)

        # Get frame data
        video_frame = data.get_video_frame()
        depth_array = data.get_depth()

        # Store for point cloud generation
        self._last_video_frame = video_frame
        self._last_depth_array = depth_array

        # Always update video stream display
        video_image = FrameProcessor.video_to_qimage(video_frame)
        self._main_window.kinect_video.setPixmap(QPixmap.fromImage(video_image))

        # Always update depth stream display (with jet colormap for better visibility)
        depth_image = FrameProcessor.depth_to_qimage(depth_array, colormap='jet')
        self._main_window.kinect_depth.setPixmap(QPixmap.fromImage(depth_image))

        # Only update point cloud if Point Cloud tab is active (performance optimization)
        if self._main_window.video_tab_widget.currentIndex() == self.TAB_POINTCLOUD:
            try:
                points, colors = FrameProcessor.depth_to_colored_pointcloud(depth_array, video_frame)
                self._pointcloud_widget.update_pointcloud(points, colors)
            except Exception as e:
                self._logger.warning(f"Point cloud error: {e}")

    def update_telemetry(self, data: TelemetryPacket):
        """Update all telemetry displays from robot data."""
        self._telemetry_count += 1

        # Motor encoders (in Locomotion section)
        self._main_window.left_encoder_lcd.display(data.left_motor.angle)
        self._main_window.right_encoder_lcd.display(data.right_motor.angle)

        # Turret data (in Turret section)
        self._main_window.turret_encoder_lcd.display(data.turret_motor.angle)
        self._main_window.color_sensor_lcd.display(data.color_sensor.raw)

        # Sensors (in Telemetry section)
        self._main_window.lcd_temperature.display(data.temperature)
        self._main_window.lcd_voltage.display(data.voltage)
        self._main_window.ultrasonic_sensor_lcd.display(data.ultrasound_sensor.raw)

        # System stats (in Telemetry section)
        stats = data.system_stats
        self._main_window.lcd_cpu.display(stats.cpu_percent)
        self._main_window.lcd_ram.display(stats.ram_percent)
        self._main_window.lcd_wifi.display(stats.net_bandwidth_mbps)

    def _setup_buttons(self):
        """Connect all button signals to handlers."""
        # Connection
        self._main_window.connect_to_robot.clicked.connect(self.on_connect_button)

        # Route commands through connection manager
        self.command_packet_signal.connect(self._connection_manager.send_command)

        # Locomotion controls
        self._main_window.forward.clicked.connect(self.go_forward)
        self._main_window.backward.clicked.connect(self.go_backward)
        self._main_window.left.clicked.connect(self.turn_left)
        self._main_window.right.clicked.connect(self.turn_right)
        self._main_window.left_full.clicked.connect(self.go_left)
        self._main_window.right_full.clicked.connect(self.go_right)

        # Turret controls
        self._main_window.turret_left.clicked.connect(self.turret_left)
        self._main_window.turret_right.clicked.connect(self.turret_right)
        self._main_window.turret_reset.clicked.connect(self.turret_reset)

    # === Command methods ===

    def go_forward(self):
        command = GoForward(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def go_backward(self):
        command = GoBackward(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def go_left(self):
        command = GoLeft(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def go_right(self):
        command = GoRight(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turn_left(self):
        command = TurnLeft(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turn_right(self):
        command = TurnRight(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)

    def turret_left(self):
        command = TurretLeft(self._main_window.turret_speed.value())
        self.command_packet_signal.emit(command)

    def turret_right(self):
        command = TurretRight(self._main_window.turret_speed.value())
        self.command_packet_signal.emit(command)

    def turret_reset(self):
        command = TurretReset()
        self.command_packet_signal.emit(command)
