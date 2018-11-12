from app.Networking.Packet import Packet

CLIENT = 1
SERVER = 2


class HelloPacket(Packet):
    def __init__(self, sequence, role, network, running, sleep):
        Packet.__init__(self, sequence)
        self._role = role
        self._running = running
        self._network = network
        self._sleep = sleep

    @property
    def sleep(self):
        return self._sleep

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        self._role = role

    def get_network(self):
        return self._network

    @property
    def running(self):
        return self._running


class HelloClientPacket(HelloPacket):
    def __init__(self, sequence, running, network, sleep):
        HelloPacket.__init__(self, sequence, role=CLIENT, running=running, network=network, sleep=sleep)


class HelloServerPacket(HelloPacket):
    def __init__(self, sequence, running, network, sleep):
        HelloPacket.__init__(self, sequence=sequence, role=SERVER, running=running, network=network, sleep=sleep)
