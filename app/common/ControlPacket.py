GO_FORWARD = 1


class ControlPacket:
    def __init__(self, action):
        self._action = action

    @property
    def action(self):
        return self._action
