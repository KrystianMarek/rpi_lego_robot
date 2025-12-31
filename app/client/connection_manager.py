"""
ConnectionManager - Manages robot connection lifecycle.

Provides:
- State machine for connection states
- Clean connect/disconnect support
- Signals for UI binding
- Centralized error handling
"""
import logging
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from app.common.config import Config


class ConnectionState(Enum):
    """Connection state machine states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ConnectionManager(QObject):
    """
    Manages the connection lifecycle to the robot.

    Signals:
        state_changed: Emitted when connection state changes
        error_occurred: Emitted when an error occurs (with message)
        telemetry_received: Forwarded from TelemetryClient
        kinect_received: Forwarded from TelemetryClient
    """

    # State signals
    state_changed = pyqtSignal(ConnectionState)
    error_occurred = pyqtSignal(str)

    # Data signals (forwarded from clients)
    telemetry_received = pyqtSignal(object)  # TelemetryPacket
    kinect_received = pyqtSignal(object)     # KinectPacket

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._state = ConnectionState.DISCONNECTED
        self._robot_ip = None

        # Client threads (lazy initialized on connect)
        self._telemetry_client = None
        self._command_client = None

    @property
    def state(self) -> ConnectionState:
        """Current connection state."""
        return self._state

    @property
    def robot_ip(self) -> str:
        """Currently connected robot IP."""
        return self._robot_ip

    @property
    def is_connected(self) -> bool:
        """True if connected to robot."""
        return self._state == ConnectionState.CONNECTED

    def _set_state(self, new_state: ConnectionState):
        """Update state and emit signal."""
        if self._state != new_state:
            self._logger.info(f"Connection state: {self._state.value} -> {new_state.value}")
            self._state = new_state
            self.state_changed.emit(new_state)

    def connect(self, robot_ip: str):
        """
        Connect to the robot at the given IP address.

        Args:
            robot_ip: IP address of the robot
        """
        if self._state == ConnectionState.CONNECTED:
            self._logger.warning("Already connected, disconnect first")
            return

        if not robot_ip:
            self.error_occurred.emit("Robot IP address is required")
            return

        self._robot_ip = robot_ip
        self._set_state(ConnectionState.CONNECTING)

        try:
            # Import here to avoid circular imports
            from app.client.gui.MainWindowWrapper import TelemetryClient, CommandClient

            # Start telemetry client
            self._telemetry_client = TelemetryClient()
            self._telemetry_client.set_robot_ip_address(robot_ip)
            self._telemetry_client.telemetry_packet_signal.connect(self._on_telemetry)
            self._telemetry_client.kinect_packet_signal.connect(self._on_kinect)
            self._telemetry_client.connection_timeout_signal.connect(self._on_connection_timeout)
            self._telemetry_client.start()

            # Start command client
            self._command_client = CommandClient(robot_ip=robot_ip)
            self._command_client.start()

            self._set_state(ConnectionState.CONNECTED)
            self._logger.info(f"Connected to robot at {robot_ip}")

        except Exception as e:
            self._logger.exception(f"Failed to connect: {e}")
            self._set_state(ConnectionState.ERROR)
            self.error_occurred.emit(str(e))
            self._cleanup_clients()

    def disconnect(self):
        """Disconnect from the robot."""
        if self._state == ConnectionState.DISCONNECTED:
            self._logger.warning("Already disconnected")
            return

        self._logger.info("Disconnecting from robot...")
        self._cleanup_clients()
        self._robot_ip = None
        self._set_state(ConnectionState.DISCONNECTED)

    def _cleanup_clients(self):
        """Stop and cleanup client threads."""
        if self._telemetry_client:
            try:
                self._telemetry_client.running = False
                self._telemetry_client.wait(2000)  # Wait up to 2 seconds
            except Exception as e:
                self._logger.warning(f"Error stopping telemetry client: {e}")
            self._telemetry_client = None

        if self._command_client:
            try:
                self._command_client.stop()
                self._command_client.wait(2000)
            except Exception as e:
                self._logger.warning(f"Error stopping command client: {e}")
            self._command_client = None

    def _on_telemetry(self, packet):
        """Forward telemetry packet."""
        self.telemetry_received.emit(packet)

    def _on_kinect(self, packet):
        """Forward kinect packet."""
        self.kinect_received.emit(packet)

    def _on_connection_timeout(self):
        """Handle connection timeout from telemetry client."""
        if self._state == ConnectionState.CONNECTED:
            self._logger.warning("Connection timeout detected")
            self._set_state(ConnectionState.ERROR)
            self.error_occurred.emit("Connection timeout - robot may be offline")

    def send_command(self, command):
        """
        Send a command to the robot.

        Args:
            command: CommandPacket to send
        """
        if not self.is_connected:
            self._logger.warning("Cannot send command: not connected")
            return

        if self._command_client:
            self._command_client.on_command_packet(command)

