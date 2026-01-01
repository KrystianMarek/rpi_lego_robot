# System Architecture

K.O.C (Kinect on Caterpillar) uses a distributed client-server architecture with ZeroMQ for high-performance messaging.

## Overview

```mermaid
flowchart TB
    subgraph CLIENT ["CLIENT (PC with PyQt5 GUI)"]
        direction TB
        subgraph GUI ["MainWindowWrapper (PyQt5 GUI)"]
            G1["Movement controls"]
            G2["Telemetry display"]
            G3["Kinect video feed"]
            G4["Sensor readings"]
        end

        CC["CommandClient\nZMQ PUSH → robot:5560\nSends movement commands"]
        TC["TelemetryClient\nZMQ SUB → robot:5559\nReceives telemetry & Kinect data"]
        HC["HelloClient\nZMQ REQ → robot:5556\nInitial handshake"]

        GUI --> CC
        GUI --> TC
        GUI --> HC
    end

    subgraph SERVER ["SERVER (Raspberry Pi 3 + BrickPi+)"]
        direction TB
        HS["HelloServer\nZMQ REP :5556"]
        HS_DESC["Handshake\nTriggers BrickPi/Kinect startup"]
        HS --- HS_DESC

        CR["CommandReceiver\nZMQ PULL :5560\n(Thread)"]
        CR_DESC["Receives commands from clients\nTranslates to motor commands\nMultiple clients supported"]
        CR --- CR_DESC

        BPW["BrickPiWrapper\nZMQ PUSH :5557\n(Thread)"]
        BPW_DESC["Motor Control & Sensor Reading\nRuns in dedicated Thread\nProcesses command queue"]
        BPW --- BPW_DESC

        KP["KinectProcess\nZMQ PUSH :5558\n(Process)"]
        KP_DESC["RGB & Depth Capture\nRuns in dedicated Process\nUses libfreenect"]
        KP --- KP_DESC

        TP["Telemetry Publisher\nZMQ PULL :5557, :5558\nZMQ PUB :5559"]
        TP_DESC["Aggregates BrickPi + Kinect data\nPublishes unified telemetry stream"]
        TP --- TP_DESC

        BPW --> TP
        KP --> TP
    end

    CLIENT <-->|"TCP/IP Network\n(only robot IP needed)"| SERVER
    HC <-->|REQ/REP| HS
    CC -->|PUSH| CR
    TP -->|PUB/SUB| TC
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

```mermaid
flowchart LR
    UI["User Input"] --> MW["MainWindowWrapper"]
    MW --> CP["CommandPacket"]
    CP --> CC["CommandClient\n(PUSH)"]
    CC -->|"connects to\nrobot:5560"| CR["CommandReceiver\n(PULL)"]
    CR --> TP["TelemetryPacket"]
    TP --> CQ["Command Queue"]
    CQ --> BPW["BrickPiWrapper"]
    BPW --> HW["BrickPi Hardware"]
    HW --> M["Motors"]
```

### Telemetry Flow (Server → Client)

```mermaid
flowchart TB
    subgraph Sources ["Data Sources"]
        BS["BrickPi Sensors"] --> BPW["BrickPiWrapper"]
        KC["Kinect Camera"] --> KP["KinectProcess"]
    end

    BPW --> TP1["TelemetryPacket"]
    KP --> KP1["KinectPacket"]

    TP1 -->|"PUSH :5557"| AGG["Telemetry Publisher\n(PULL)"]
    KP1 -->|"PUSH :5558"| AGG

    AGG --> PUB["Aggregator"]
    PUB -->|"PUB :5559"| TC["TelemetryClient\n(SUB)"]
    TC --> MW["MainWindowWrapper"]
    MW --> GUI["GUI Display"]
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
