"""
Serialization utilities for network communication.

Provides compress/decompress functions for sending Python objects
over ZMQ sockets using pickle and zlib compression.

Formerly named Misc.py.
"""
import pickle
import zlib

from app.networking import TelemetryPacket

# Use protocol 4 for compatibility with Python 3.4+
# (Protocol 5 requires Python 3.8+ which older Raspberry Pi images may lack)
PICKLE_PROTOCOL = 4


def compress(data: object) -> bytes:
    """Compress a Python object for network transmission."""
    p = pickle.dumps(data, protocol=PICKLE_PROTOCOL)
    return zlib.compress(p)


def decompress(data: bytes) -> object:
    """Decompress received network data back to Python object."""
    p = zlib.decompress(data)
    return pickle.loads(p)


def decompress_telemetry(data: bytes) -> TelemetryPacket:
    """Decompress data expecting a TelemetryPacket."""
    return decompress(data)


def print_send(data: object) -> str:
    """Format a debug message for sent packets."""
    return "sending {}, sequence {}".format(data.__class__.__name__, data.sequence)


def print_recv(data: object) -> str:
    """Format a debug message for received packets."""
    return "receiving {}, sequence {}".format(data.__class__.__name__, data.sequence)

