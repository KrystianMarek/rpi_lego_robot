"""
MainWindowWrapper - PyQt5 GUI for controlling the robot.
"""
import logging

import zmq
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QDialog

from app.client.connection_manager import ConnectionManager, ConnectionState
from app.client.frame_processor import FrameProcessor
from app.client.HelloClient import HelloClient
from app.common.config import Config
from app.Networking.CommandPacket import CommandPacket, TurnLeft, TurnRight, \
    TurretLeft, TurretRight, GoForward, GoBackward, GoLeft, GoRight, TurretReset
from app.Networking.KinectPacket import KinectPacket
from app.Networking.TelemetryPacket import TelemetryPacket
from app.client.gui.main_window import Ui_MainWindow
from app.common.Misc import decompress, compress


class CommandClient(QtCore.QThread):
    """
    Sends commands to the robot via ZMQ PUSH socket.

    Connects to the robot's CommandReceiver (PULL socket).
    This is the inverse of the old design where the robot connected to the client.
    """

    def __init__(self, robot_ip: str, port: int = None, parent=None):
        if port is None:
            port = Config.COMMAND_PORT
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger(__name__)
        self._running = True
        self._robot_ip = robot_ip
        self._port = port
        self._context = zmq.Context()
        self._sender = self._context.socket(zmq.PUSH)

        # Connect to robot's command receiver
        address = "tcp://{}:{}".format(robot_ip, port)
        self._sender.connect(address)
        self._logger.info("CommandClient connected to {}".format(address))

    def on_command_packet(self, packet: CommandPacket):
        """Send a command packet to the robot."""
        try:
            self._sender.send(compress(packet))
        except Exception as e:
            self._logger.exception(e)

    def run(self):
        """Keep thread alive while running."""
        while self._running:
            QtCore.QThread.msleep(100)

        self._sender.close()
        self._context.term()

    def stop(self):
        """Stop the command client."""
        self._running = False


class TelemetryClient(QtCore.QThread):

    telemetry_packet_signal = pyqtSignal(TelemetryPacket)
    kinect_packet_signal = pyqtSignal(KinectPacket)

    def __init__(self, port: int = None, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._logger = logging.getLogger(__name__)
        self._robot_ip_address = ''
        self._port = port if port is not None else Config.TELEMETRY_PORT

        self._hello_client = None

        self.running = True
        self.ultrasonic_sensor = 0
        self.color_sensor = 0

    def robot_ip_address(self):
        return self._robot_ip_address

    def set_robot_ip_address(self, ip):
        self._robot_ip_address = ip

    def launch_hello_client(self):
        self._hello_client = HelloClient(self._robot_ip_address, Config.HELLO_PORT)
        self._hello_client.start()

    def on_telemetry_packet(self, packet: TelemetryPacket):
        self.telemetry_packet_signal = packet

    def run(self):
        self.launch_hello_client()

        context = zmq.Context()
        # First, connect our subscriber socket
        zmq_address = "tcp://{}:{}".format(self._robot_ip_address, self._port)
        self._logger.debug("ZMQ connecting to {}".format(zmq_address))
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(zmq_address)
        subscriber.setsockopt(zmq.SUBSCRIBE, b'')

        while self.running:
            try:
                data = decompress(subscriber.recv())
                if type(data) is TelemetryPacket:
                    self.telemetry_packet_signal.emit(data)
                if type(data) is KinectPacket:
                    self.kinect_packet_signal.emit(data)

            except Exception as e:
                self._logger.exception(e)
                break

        self._hello_client.wait()
        subscriber.close()
        context.term()


class MainWindowWrapper(QDialog):

    command_packet_signal = pyqtSignal(CommandPacket)

    def __init__(self, app, main_window: QMainWindow, default_robot_ip: str = ''):
        QDialog.__init__(self)
        self._logger = logging.getLogger(__name__)
        self._main_window = Ui_MainWindow()
        self._main_window.setupUi(main_window)
        self._main_window_ref = main_window  # Keep reference for status bar
        self._app = app

        # Frame counters
        self._video_frame_count = 0
        self._depth_frame_count = 0
        self._telemetry_count = 0

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

        self.setup_buttons()
        self._setup_stats_display()

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

    def _setup_stats_display(self):
        """Add status bar for system stats display."""
        from PyQt5.QtWidgets import QStatusBar, QLabel

        # Create status bar
        self._status_bar = QStatusBar()
        self._main_window_ref.setStatusBar(self._status_bar)

        # Create labels for stats
        self._stats_label = QLabel("CPU: --% | RAM: --% | WiFi: -- Mbps")
        self._frames_label = QLabel("Video: 0 | Depth: 0")

        self._status_bar.addWidget(self._stats_label)
        self._status_bar.addPermanentWidget(self._frames_label)

    def update_kinect(self, data: KinectPacket):
        self._logger.debug("Got kinect packet!")

        # Update frame counters
        self._video_frame_count += 1
        self._depth_frame_count += 1

        # Display RGB video frame
        video_frame = data.get_video_frame()
        video_image = FrameProcessor.video_to_qimage(video_frame)
        self._main_window.kinect_video.setPixmap(QPixmap.fromImage(video_image))

        # Display depth frame (using grayscale colormap)
        # TODO: Add UI toggle for colormap selection (grayscale/jet/viridis)
        depth_array = data.get_depth()
        depth_image = FrameProcessor.depth_to_qimage(depth_array, colormap='grayscale')
        self._main_window.label_10.setPixmap(QPixmap.fromImage(depth_image))

        # Update frame counter display
        self._frames_label.setText(f"Video: {self._video_frame_count} | Depth: {self._depth_frame_count}")

    def update_telemetry(self, data: TelemetryPacket):
        # self._logger.debug("Got telemetry packet!")
        self._telemetry_count += 1

        # Update sensor displays
        self._main_window.color_sensor_lcd.display(data.color_sensor.raw)
        self._main_window.ultrasonic_sensor_lcd.display(data.ultrasound_sensor.raw)
        self._main_window.lcd_temperature.display(data.temperature)
        self._main_window.lcd_voltage.display(data.voltage)

        self._main_window.left_encoder_lcd.display(data.left_motor.angle)
        self._main_window.right_encoder_lcd.display(data.right_motor.angle)
        self._main_window.turret_encoder_lcd.display(data.turret_motor.angle)

        # Update system stats display
        stats = data.system_stats
        self._stats_label.setText(
            f"CPU: {stats.cpu_percent:.1f}% | "
            f"RAM: {stats.ram_percent:.1f}% ({stats.ram_used_mb:.0f}MB) | "
            f"WiFi: {stats.net_bandwidth_mbps:.2f} Mbps"
        )

    def setup_buttons(self):
        self._main_window.connect_to_robot.clicked.connect(self.on_connect_button)

        # Route commands through connection manager
        self.command_packet_signal.connect(self._connection_manager.send_command)

        self._main_window.forward.clicked.connect(self.go_forward)
        self._main_window.backward.clicked.connect(self.go_backward)

        self._main_window.left.clicked.connect(self.turn_left)
        self._main_window.right.clicked.connect(self.turn_right)
        self._main_window.left_full.clicked.connect(self.go_left)
        self._main_window.right_full.clicked.connect(self.go_right)

        self._main_window.turret_left.clicked.connect(self.turret_left)
        self._main_window.turret_right.clicked.connect(self.turret_right)

        self._main_window.turret_reset.clicked.connect(self.turret_reset)

    def go_forward(self):
        command = GoForward(self._main_window.motor_speed.value())
        self.command_packet_signal.emit(command)
        # self._logger.debug(command)

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
