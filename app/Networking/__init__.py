import logging
import netifaces

from .HelloPacket import *
from .Packet import *

logger = logging.getLogger(__name__)


def get_available_interfaces():
    result = {}
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        try:
            address = netifaces.ifaddresses(interface)
            result[interface] = address[netifaces.AF_INET][0]
        except Exception as e:
            logger.exception(e)

    result['default'] = netifaces.gateways()['default'][netifaces.AF_INET][1]

    return result
