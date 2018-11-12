import pickle
import zlib

from app.Networking.TelemetryPacket import TelemetryPacket


def compress(data: object):
    p = pickle.dumps(data)
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
