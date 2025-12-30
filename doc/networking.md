# Networking Protocol

## Overview

K.O.C uses ZeroMQ for all network communication with Python's `pickle` for serialization and `zlib` for compression.

**Key Design**: Client only needs the robot's IP address. All connections flow from client to robot.

## Serialization

All packets are serialized using pickle protocol 4 (compatible with Python 3.4+):

```python
# Compress (send)
data = zlib.compress(pickle.dumps(packet, protocol=4))

# Decompress (receive)
packet = pickle.loads(zlib.decompress(data))
```

**Security Note**: Pickle is used for convenience in a trusted network environment. Do not expose these ports to untrusted networks.

## Port Configuration

| Port | Socket Type | Binds | Connects | Purpose |
|------|-------------|-------|----------|---------|
| 5556 | REP/REQ | Robot | Client | Handshake |
| 5559 | PUB/SUB | Robot | Client | Telemetry/Video |
| 5560 | PULL/PUSH | Robot | Client | Commands |

## Packet Types

### Base Packet

All packets inherit from the base `Packet` class:

```python
class Packet:
    sequence: int    # Packet sequence number
    time: float      # Timestamp (time.time())
```

### HelloClientPacket

Sent by client during handshake.

| Field | Type | Description |
|-------|------|-------------|
| sequence | int | Packet sequence (starts at 1) |
| network | dict | Client network interfaces (informational) |

### HelloServerPacket

Server response to hello.

| Field | Type | Description |
|-------|------|-------------|
| sequence | int | Client sequence + 1 |
| running | bool | Server operational status |
| network | dict | Server network interfaces |
| sleep | float | Heartbeat interval |

### CommandPacket

Movement commands from client to server.

| Field | Type | Description |
|-------|------|-------------|
| command | int | Command type constant |
| value | int | Speed/intensity (0-255) |

#### Command Constants

| Constant | Value | Description |
|----------|-------|-------------|
| GO_FORWARD | 1 | Move forward |
| GO_BACKWARD | 2 | Move backward |
| GO_LEFT | 3 | Curve left (differential) |
| GO_RIGHT | 4 | Curve right (differential) |
| TURN_LEFT | 5 | Pivot turn left |
| TURN_RIGHT | 6 | Pivot turn right |
| TURRET_RIGHT | 7 | Rotate turret right |
| TURRET_LEFT | 8 | Rotate turret left |
| TURRET_RESET | 9 | Reset turret position |

#### Command Subclasses

Each command has a dedicated class:
- `GoForward(value)`
- `GoBackward(value)`
- `GoLeft(value)`
- `GoRight(value)`
- `TurnLeft(value)`
- `TurnRight(value)`
- `TurretLeft(value)`
- `TurretRight(value)`
- `TurretReset()`

### TelemetryPacket

Sensor and motor state from server.

| Field | Type | Description |
|-------|------|-------------|
| left_motor | LegoMotor | Left drive motor state |
| right_motor | LegoMotor | Right drive motor state |
| turret_motor | LegoMotor | Turret motor state |
| color_sensor | LegoSensor | Color/light sensor reading |
| ultrasound_sensor | LegoSensor | Distance sensor reading |
| voltage | float | Battery voltage |
| temperature | float | CPU temperature (°C) |

#### LegoMotor

| Field | Type | Description |
|-------|------|-------------|
| port | int | BrickPi port constant |
| speed | int | Current speed (-255 to 255) |
| desired_speed | int | Target speed |
| angle | int | Encoder position |

#### LegoSensor

| Field | Type | Description |
|-------|------|-------------|
| port | int | BrickPi port constant |
| raw | int | Raw sensor value |

### KinectPacket

Video and depth frames from Kinect.

| Field | Type | Description |
|-------|------|-------------|
| video_frame | numpy.ndarray | RGB image (480×640×3) |
| depth | numpy.ndarray | Depth map (480×640) |
| tilt_state | int | Tilt motor state (not implemented) |
| tilt_degs | int | Tilt angle (not implemented) |

## Protocol Flows

### Connection Handshake

```
Client                              Server
   │                                   │
   │──── HelloClientPacket(seq=1) ────>│  (REQ → REP :5556)
   │                                   │
   │<─── HelloServerPacket(seq=2) ─────│
   │     {running: true}               │
   │                                   │
   │     [Server starts BrickPi/Kinect]│
   │                                   │
```

### Command Transmission

```
Client                              Server
   │                                   │
   │──── CommandPacket ───────────────>│  (PUSH → PULL :5560)
   │     {command: GO_FORWARD,         │
   │      value: 200}                  │
   │                                   │
   │     [CommandReceiver receives]    │
   │     [Converts to TelemetryPacket] │
   │     [Queues for BrickPiWrapper]   │
   │                                   │
```

### Telemetry Stream

```
Client                              Server
   │                                   │
   │<─── TelemetryPacket ─────────────│  (SUB ← PUB :5559)
   │     {motors, sensors, temp, ...}  │
   │                                   │
   │<─── KinectPacket ────────────────│
   │     {video_frame, depth}          │
   │                                   │
   │     [Repeats at ~10Hz]            │
   │                                   │
```

## Command Translation

The `CommandReceiver` translates high-level commands to motor speeds:

| Command | Left Motor | Right Motor | Turret |
|---------|------------|-------------|--------|
| GoForward(v) | -v | +v | 0 |
| GoBackward(v) | +v | -v | 0 |
| GoLeft(v) | -v/2 | +v | 0 |
| GoRight(v) | -v | +v/2 | 0 |
| TurnLeft(v) | -v | -v | 0 |
| TurnRight(v) | +v | +v | 0 |
| TurretLeft(v) | 0 | 0 | +v |
| TurretRight(v) | 0 | 0 | -v |

## Multiple Client Support

The PUSH/PULL pattern on port 5560 allows multiple clients to send commands:

- Robot binds PULL socket (accepts connections from any client)
- Each client connects PUSH socket to robot
- ZMQ provides fair queuing of commands from all clients
- No configuration needed — just connect and send

## Error Handling

- All network operations are wrapped in try/except blocks
- KeyboardInterrupt triggers graceful shutdown
- Socket errors break the main loop and trigger cleanup
- ZMQ contexts and sockets are properly terminated on exit

## Performance Considerations

- **Compression**: zlib reduces bandwidth for large Kinect frames
- **Polling**: ZMQ Poller handles multiple sockets efficiently
- **Queuing**: Command queue has max size of 100 to prevent memory issues
- **Grace period**: 3-cycle grace period prevents motor stuttering on command gaps
- **Pickle protocol 4**: Compatible with Python 3.4+ for cross-version support
