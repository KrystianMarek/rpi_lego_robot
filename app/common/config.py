"""
Central configuration for K.O.C Robot.

All ports, timeouts, and calibration values in one place.
Values can be overridden via environment variables.
"""
import os


def _env_int(key: str, default: int) -> int:
    """Get integer from environment variable with default."""
    return int(os.environ.get(key, default))


def _env_float(key: str, default: float) -> float:
    """Get float from environment variable with default."""
    return float(os.environ.get(key, default))


def _env_str(key: str, default: str) -> str:
    """Get string from environment variable with default."""
    return os.environ.get(key, default)


class Config:
    """Robot configuration constants."""

    # ==========================================================================
    # Network Ports
    # ==========================================================================

    # REQ/REP handshake port (HelloServer/HelloClient)
    HELLO_PORT = _env_int('HELLO_PORT', 5556)

    # Internal ports (server-side only, localhost)
    BRICKPI_PORT = _env_int('BRICKPI_PORT', 5557)  # BrickPi → Aggregator
    KINECT_PORT = _env_int('KINECT_PORT', 5558)    # Kinect → Aggregator

    # External ports (client-facing)
    TELEMETRY_PORT = _env_int('TELEMETRY_PORT', 5559)  # PUB: server → clients
    COMMAND_PORT = _env_int('COMMAND_PORT', 5560)      # PULL: clients → server

    # ==========================================================================
    # Connection Settings
    # ==========================================================================

    # Robot IP address (client only)
    ROBOT_IP = _env_str('ROBOT_IP', '')

    # Localhost for internal communication
    LOCALHOST = '127.0.0.1'

    # ==========================================================================
    # Timing
    # ==========================================================================

    # BrickPi update interval (seconds)
    BRICKPI_CLOCK = _env_float('BRICKPI_CLOCK', 0.1)

    # HelloServer sleep between handshakes (seconds)
    HELLO_SLEEP = _env_float('HELLO_SLEEP', 1.0)

    # Command queue max size
    COMMAND_QUEUE_SIZE = _env_int('COMMAND_QUEUE_SIZE', 100)

    # ==========================================================================
    # Kinect Calibration (for point cloud conversion)
    # ==========================================================================

    # Focal lengths (pixels)
    KINECT_FX = _env_float('KINECT_FX', 594.21)
    KINECT_FY = _env_float('KINECT_FY', 591.04)

    # Principal point (pixels)
    KINECT_CX = _env_float('KINECT_CX', 339.5)
    KINECT_CY = _env_float('KINECT_CY', 242.7)

    # ==========================================================================
    # Depth Processing
    # ==========================================================================

    # Raw depth range (11-bit sensor)
    DEPTH_MAX = 2047
    DEPTH_MIN_VALID = 400   # ~0.5m in raw units
    DEPTH_MAX_VALID = 4000  # ~4m in raw units

    # Display normalization
    DEPTH_DISPLAY_BITS = 10  # Clip to 10 bits before >> 2 to 8-bit

