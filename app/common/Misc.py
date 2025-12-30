import pickle
import zlib

from app.Networking.TelemetryPacket import TelemetryPacket

# Use protocol 4 for compatibility with Python 3.4+
# (Protocol 5 requires Python 3.8+ which older Raspberry Pi images may lack)
PICKLE_PROTOCOL = 4


def compress(data: object):
    p = pickle.dumps(data, protocol=PICKLE_PROTOCOL)
    return zlib.compress(p)


def decompress(data: object):
    p = zlib.decompress(data)
    return pickle.loads(p)


def decompress_telemetry(data: object) -> TelemetryPacket:
    return decompress(data)


def print_send(data: object):
    return "sending {}, sequence {}".format(data.__class__.__name__, data.sequence)


def print_recv(data: object):
    return "receiving {}, sequence {}".format(data.__class__.__name__, data.sequence)
