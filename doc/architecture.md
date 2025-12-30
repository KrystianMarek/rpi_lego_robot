# System Architecture

K.O.C (Kinect on Caterpillar) uses a distributed client-server architecture with ZeroMQ for high-performance messaging.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT (PC with PyQt5 GUI)                                                 │
│                                                                             │
│  ┌───────────────────────┐      ┌─────────────────────────────────────────┐ │
│  │   MainWindowWrapper   │──────│  CommandClient                          │ │
│  │   (PyQt5 GUI)         │      │  ZMQ PUSH connects to robot:5560        │ │
│  │                       │      │  Sends movement commands                │ │
│  │  - Movement controls  │      └─────────────────────────────────────────┘ │
│  │  - Telemetry display  │                                                  │
│  │  - Kinect video feed  │      ┌─────────────────────────────────────────┐ │
│  │  - Sensor readings    │      │  TelemetryClient                        │ │
│  └───────────────────────┘      │  ZMQ SUB connects to robot:5559         │ │
│                                 │  Receives telemetry & Kinect data       │ │
│                                 └─────────────────────────────────────────┘ │
│                                 ┌─────────────────────────────────────────┐ │
│                                 │  HelloClient                            │ │
│                                 │  ZMQ REQ connects to robot:5556         │ │
│                                 │  Initial handshake                      │ │
│                                 └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ TCP/IP Network
                                        │ (only robot IP needed)
                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│  SERVER (Raspberry Pi 3 + BrickPi+)                                         │
│                                                                             │
│  ┌────────────────────┐         ┌───────────────────────────────────────┐   │
│  │  HelloServer       │─────────│  Handshake                            │   │
│  │  ZMQ REP :5556     │         │  Triggers BrickPi/Kinect startup      │   │
│  └────────────────────┘         └───────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────┐         ┌───────────────────────────────────────┐   │
│  │  CommandReceiver   │─────────│  Receives commands from clients       │   │
│  │  ZMQ PULL :5560    │         │  Translates to motor commands         │   │
│  │  (Thread)          │         │  Multiple clients supported           │   │
│  └────────────────────┘         └───────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────┐         ┌───────────────────────────────────────┐   │
│  │  BrickPiWrapper    │─────────│  Motor Control & Sensor Reading       │   │
│  │  ZMQ PUSH :5557    │         │  Runs in dedicated Thread             │   │
│  │  (Thread)          │         │  Processes command queue              │   │
│  └────────────────────┘         └───────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────┐         ┌───────────────────────────────────────┐   │
│  │  KinectProcess     │─────────│  RGB & Depth Capture                  │   │
│  │  ZMQ PUSH :5558    │         │  Runs in dedicated Process            │   │
│  │  (Process)         │         │  Uses libfreenect                     │   │
│  └────────────────────┘         └───────────────────────────────────────┘   │
│                                                                             │
│  ┌────────────────────┐         ┌───────────────────────────────────────┐   │
│  │  Telemetry Publisher│────────│  Aggregates BrickPi + Kinect data     │   │
│  │  ZMQ PULL :5557    │         │  Publishes unified telemetry stream   │   │
│  │  ZMQ PULL :5558    │         │                                       │   │
│  │  ZMQ PUB  :5559    │         │                                       │   │
│  └────────────────────┘         └───────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Design Principles

1. **Client only needs robot IP** — all connections flow from client to robot
2. **Multiple clients supported** — robot accepts commands from any connected client
3. **No reverse connections** — robot never dials back to client

## ZeroMQ Patterns

The system uses three ZeroMQ messaging patterns:

### REQ/REP (Request-Reply)
- **Port 5556**: HelloServer ↔ HelloClient
- Used for initial handshake
- Triggers hardware startup on first client connection

### PUB/SUB (Publish-Subscribe)
- **Port 5559**: Server → Clients (telemetry stream)
- One-to-many broadcast of sensor data and video

### PUSH/PULL (Pipeline)
- **Port 5560**: Clients → Server (commands)
- **Port 5557**: BrickPiWrapper → Telemetry Publisher (internal)
- **Port 5558**: KinectProcess → Telemetry Publisher (internal)

## Data Flow

### Startup Sequence

1. Server starts and binds all ports (:5556, :5559, :5560)
2. CommandReceiver starts immediately (no client dependency)
3. Client GUI launches and enters robot IP
4. Client connects to robot on all ports
5. HelloClient triggers BrickPi and Kinect startup on first connection
6. Data flows begin

### Command Flow (Client → Server)

```
User Input → MainWindowWrapper → CommandPacket → CommandClient (PUSH)
    ↓
    ↓ connects to robot:5560
    ↓
CommandReceiver (PULL) → TelemetryPacket → Command Queue
    ↓
BrickPiWrapper → BrickPi Hardware → Motors
```

### Telemetry Flow (Server → Client)

```
BrickPi Sensors → BrickPiWrapper → TelemetryPacket → PUSH :5557
Kinect Camera   → KinectProcess  → KinectPacket   → PUSH :5558
    ↓
Telemetry Publisher (PULL) → Aggregator → PUB :5559
    ↓
TelemetryClient (SUB) → MainWindowWrapper → GUI Display
```

## Threading Model

| Component | Type | Purpose |
|-----------|------|---------|
| HelloServer | Thread (daemon) | Connection handshake |
| CommandReceiver | Thread (daemon) | Receive commands from clients |
| BrickPiWrapper | Thread (daemon) | Motor/sensor I/O |
| KinectProcess | Process (daemon) | Camera capture (CPU-intensive) |
| Telemetry Publisher | Main thread | Data aggregation |

The Kinect runs in a separate **Process** rather than a Thread to avoid GIL contention during image processing.

## Configuration

### Network Ports

| Port | Protocol | Direction | Purpose |
|------|----------|-----------|---------|
| 5556 | REQ/REP | Client → Robot | Hello/Handshake |
| 5557 | PUSH/PULL | Internal | BrickPi → Aggregator |
| 5558 | PUSH/PULL | Internal | Kinect → Aggregator |
| 5559 | PUB/SUB | Robot → Clients | Telemetry broadcast |
| 5560 | PUSH/PULL | Clients → Robot | Command input |

### Timing

- BrickPi update clock: 100ms (configurable)
- Temperature/voltage polling: Every 50 cycles (~5 seconds)
- HelloServer sleep: 1 second between heartbeats
