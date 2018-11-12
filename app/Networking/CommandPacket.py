from app.Networking import Packet

GO_FORWARD = 1
GO_BACKWARD = 2
GO_LEFT = 3
GO_RIGHT = 4
TURN_LEFT = 5
TURN_RIGHT = 6
TURRET_RIGHT = 7
TURRET_LEFT = 8
TURRET_RESET = 9


class CommandPacket(Packet):
    def __init__(self, command, value):
        Packet.__init__(self, 0)

        self._command = command
        self._value = value

    @property
    def command(self):
        return self._command

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return repr("command: {}, value: {}".format(self._command, self._value))


class GoForward(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, GO_FORWARD, value)


class GoBackward(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, GO_BACKWARD, value)


class GoLeft(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, GO_LEFT, value)


class GoRight(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, GO_RIGHT, value)


class TurnLeft(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, TURN_LEFT, value)


class TurnRight(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, TURN_RIGHT, value)


class TurretLeft(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, TURRET_LEFT, value)


class TurretRight(CommandPacket):
    def __init__(self, value):
        CommandPacket.__init__(self, TURRET_RIGHT, value)


class TurretReset(CommandPacket):
    def __init__(self):
        CommandPacket.__init__(self, TURRET_RESET, 0)
