# Code Cleanup & Naming Refactor TODO

## Analysis Summary

**Date:** 2026-01-01
**Scope:** Codebase-wide naming improvements and packet class consolidation

### Goals

1. **Primary:** Rename poorly-named classes and modules to reflect their actual purpose
2. **Primary:** Consolidate scattered packet/data classes into a cleaner structure
3. **Secondary:** Remove dead code and deprecated files
4. **Secondary:** Fix naming convention inconsistencies (PascalCase vs snake_case)

---

## Current Problems

### 1. Misleading "Hello" Naming Convention

The "Hello" prefix doesn't describe what these classes actually do:

| Current Name | Actual Purpose | Suggested Name |
|--------------|----------------|----------------|
| `HelloClient` | Sends heartbeat/keepalive to server | `HeartbeatClient` |
| `HelloServer` | Receives heartbeat, triggers component startup | `HandshakeServer` |
| `HelloPacket` | Heartbeat packet base class | `HeartbeatPacket` |
| `HelloClientPacket` | Client heartbeat request | `HeartbeatRequest` |
| `HelloServerPacket` | Server heartbeat response | `HeartbeatResponse` |

**Files affected:**
- `app/client/HelloClient.py` → `app/client/heartbeat_client.py`
- `app/server/HelloServer.py` → `app/server/handshake_server.py`
- `app/Networking/HelloPacket.py` → merge into consolidated packets module

### 2. Scattered Packet Classes

Packet/data classes are spread across 5+ files with no clear organization:

```
app/Networking/
├── Packet.py           # Base Packet class (20 lines)
├── HelloPacket.py      # HelloPacket + 2 subclasses (43 lines)
├── CommandPacket.py    # CommandPacket + 9 command classes (76 lines)
├── KinectPacket.py     # KinectPacket (23 lines)
└── TelemetryPacket.py  # TelemetryPacket + LegoMotor + LegoSensor + SystemStats (207 lines)

app/common/
└── ControlPacket.py    # Duplicate/dead code (11 lines)
```

**Issues:**
- Small files with only 1-2 classes each
- `TelemetryPacket.py` contains 4 unrelated classes (SystemStats, LegoMotor, LegoSensor, TelemetryPacket)
- `ControlPacket.py` appears to be dead code (duplicate of CommandPacket)
- Hard to find which file contains which class

### 3. Inconsistent Naming Conventions

| Issue | Examples |
|-------|----------|
| **Folder case** | `Networking/` (PascalCase) vs `client/`, `server/`, `common/` (snake_case) |
| **Method style** | `KinectPacket.get_video_frame()` vs `TelemetryPacket.left_motor` (property) |
| **File names** | `HelloClient.py` (PascalCase) vs `connection_manager.py` (snake_case) |

### 4. Classes in Wrong Modules

```python
# MainWindowWrapper.py contains:
class CommandClient(QtCore.QThread):  # Lines 25-66 - should be separate module
class TelemetryClient(QtCore.QThread): # Lines 69-152 - should be separate module
class MainWindowWrapper(QDialog):      # Lines 155-420 - belongs here
```

These network client classes don't belong in a GUI wrapper module.

### 5. Vague Module Names

| Current | Purpose | Suggested |
|---------|---------|-----------|
| `Misc.py` | Serialization (compress/decompress) | `serialization.py` |
| `ControlPacket.py` | Dead code | DELETE |

### 6. Deprecated Files

- `app/client/gui/main_window.ui` - No longer used after GUI refactor (main_window.py is now manually maintained)

---

## Proposed Structure

### Option A: Consolidated Packets Module

```
app/
├── client/
│   ├── __init__.py
│   ├── heartbeat_client.py      # renamed from HelloClient.py
│   ├── telemetry_client.py      # extracted from MainWindowWrapper
│   ├── command_client.py        # extracted from MainWindowWrapper
│   ├── connection_manager.py
│   ├── frame_processor.py
│   ├── pointcloud_widget.py
│   └── gui/
│       ├── main_window.py
│       └── MainWindowWrapper.py  # now just UI logic
│
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_wrapper.py       # renamed from LoggingWrapper.py
│   └── serialization.py         # renamed from Misc.py
│
├── networking/                   # renamed from Networking/ (lowercase)
│   ├── __init__.py
│   └── packets.py               # ALL packet classes consolidated
│
└── server/
    ├── __init__.py
    ├── handshake_server.py      # renamed from HelloServer.py
    ├── command_receiver.py      # renamed from CommandReceiver.py
    ├── brickpi_wrapper.py       # renamed from BrickPiWrapper.py
    └── kinect_process.py        # renamed from KinectProcess.py
```

### Option B: Packets Sub-Package (if too large)

```
app/networking/
├── __init__.py
└── packets/
    ├── __init__.py       # exports all packet classes
    ├── base.py           # Packet base class
    ├── heartbeat.py      # HeartbeatPacket, HeartbeatRequest, HeartbeatResponse
    ├── command.py        # CommandPacket and command subclasses
    ├── telemetry.py      # TelemetryPacket, LegoMotor, LegoSensor, SystemStats
    └── kinect.py         # KinectPacket
```

**Recommendation:** Start with Option A (single `packets.py`). Split later if it grows too large.

---

## TODO Tasks

### Phase 1: Extract Client Classes from MainWindowWrapper

- [ ] **1.1** Create `app/client/telemetry_client.py`
  - Move `TelemetryClient` class from `MainWindowWrapper.py`
  - Update imports in `MainWindowWrapper.py` and `connection_manager.py`

- [ ] **1.2** Create `app/client/command_client.py`
  - Move `CommandClient` class from `MainWindowWrapper.py`
  - Update imports

- [ ] **1.3** Update `MainWindowWrapper.py`
  - Remove extracted classes
  - Import from new locations
  - Now contains only `MainWindowWrapper` class

### Phase 2: Consolidate Packet Classes

- [ ] **2.1** Create `app/networking/packets.py`
  - Combine all packet classes into single module
  - Organize with clear section comments
  - Keep backward-compatible imports in `__init__.py`

- [ ] **2.2** Structure of consolidated `packets.py`:
  ```python
  # === Base ===
  class Packet: ...

  # === Heartbeat (formerly Hello) ===
  class HeartbeatPacket: ...
  class HeartbeatRequest: ...  # formerly HelloClientPacket
  class HeartbeatResponse: ... # formerly HelloServerPacket

  # === Commands ===
  class CommandPacket: ...
  class GoForward: ...
  # ... other commands

  # === Telemetry Data Classes ===
  class SystemStats: ...
  class LegoMotor: ...
  class LegoSensor: ...
  class TelemetryPacket: ...

  # === Kinect ===
  class KinectPacket: ...
  ```

- [ ] **2.3** Update `app/networking/__init__.py`
  - Export all packet classes for backward compatibility
  - Remove old imports from individual files

- [ ] **2.4** Delete old packet files (after verification)
  - `Packet.py`
  - `HelloPacket.py`
  - `CommandPacket.py`
  - `TelemetryPacket.py`
  - `KinectPacket.py`

### Phase 3: Rename "Hello" Classes

- [ ] **3.1** Rename `HelloClient` → `HeartbeatClient`
  - Rename file: `HelloClient.py` → `heartbeat_client.py`
  - Rename class inside
  - Update all imports

- [ ] **3.2** Rename `HelloServer` → `HandshakeServer`
  - Rename file: `HelloServer.py` → `handshake_server.py`
  - Rename class inside
  - Update all imports (including `server.py`)

- [ ] **3.3** Rename packet classes in consolidated module
  - `HelloPacket` → `HeartbeatPacket`
  - `HelloClientPacket` → `HeartbeatRequest`
  - `HelloServerPacket` → `HeartbeatResponse`
  - Keep type aliases for backward compatibility if needed

### Phase 4: Fix Naming Conventions

- [ ] **4.1** Rename `Networking/` → `networking/`
  - Lowercase folder name to match Python conventions
  - Update all imports across codebase

- [x] **4.2** Rename remaining PascalCase files to snake_case
  - `BrickPiWrapper.py` → `brick_pi_wrapper.py`
  - `CommandReceiver.py` → `command_receiver.py`
  - `KinectProcess.py` → `kinect_process.py`
  - `LoggingWrapper.py` → `logging_wrapper.py`
  - `MainWindowWrapper.py` → keep as is (common Qt pattern)

- [ ] **4.3** Rename `Misc.py` → `serialization.py`
  - Better describes the compress/decompress utilities

### Phase 5: Cleanup Dead Code

- [ ] **5.1** Delete `app/common/ControlPacket.py`
  - Verify it's not imported anywhere
  - Remove file

- [ ] **5.2** Delete or archive `app/client/gui/main_window.ui`
  - No longer used (main_window.py is manually maintained)
  - Either delete or move to `doc/archive/`

### Phase 6: Standardize Property Style

- [ ] **6.1** Update `KinectPacket` to use properties
  - Change `get_video_frame()` → `video_frame` property
  - Change `get_depth()` → `depth` property
  - Change `get_tilt_state()` → `tilt_state` property
  - Change `get_tilt_degs()` → `tilt_degs` property

- [ ] **6.2** Update all call sites
  - `data.get_video_frame()` → `data.video_frame`
  - `data.get_depth()` → `data.depth`

### Phase 7: Update Imports & Testing

- [ ] **7.1** Update all import statements across codebase
- [ ] **7.2** Run application to verify nothing is broken
- [ ] **7.3** Update `Config` class comments for renamed ports/classes

---

## Implementation Notes

### Backward Compatibility Strategy

To avoid breaking imports during transition, use re-exports in `__init__.py`:

```python
# app/networking/__init__.py
from .packets import (
    Packet,
    HeartbeatPacket, HeartbeatRequest, HeartbeatResponse,
    CommandPacket, GoForward, GoBackward, GoLeft, GoRight,
    TurnLeft, TurnRight, TurretLeft, TurretRight, TurretReset,
    TelemetryPacket, LegoMotor, LegoSensor, SystemStats,
    KinectPacket,
)

# Backward compatibility aliases
HelloPacket = HeartbeatPacket
HelloClientPacket = HeartbeatRequest
HelloServerPacket = HeartbeatResponse
```

### Testing Each Phase

After each phase:
1. Run `python -c "from app.networking import *"` to verify imports
2. Run `python gui.py` to verify client works
3. (If robot available) Run `python server.py` to verify server works

### Files to Update (Import Changes)

Key files that will need import updates:
- `gui.py`
- `server.py`
- `app/client/gui/MainWindowWrapper.py`
- `app/client/connection_manager.py`
- `app/server/CommandReceiver.py`
- `app/server/BrickPiWrapper.py`
- `app/common/Misc.py` (imports TelemetryPacket)

---

## Priority Order

1. **High:** Phase 1 (Extract clients) - cleanest separation of concerns
2. **High:** Phase 2 (Consolidate packets) - major code organization win
3. **Medium:** Phase 3 (Rename Hello→Heartbeat) - clarity improvement
4. **Medium:** Phase 4 (Naming conventions) - consistency
5. **Low:** Phase 5 (Dead code) - cleanup
6. **Low:** Phase 6 (Property style) - consistency polish
7. **Required:** Phase 7 (Testing) - verification

---

## Implementation Status

**Date Completed:** 2026-01-01

### Completed Changes

#### Phase 1: Extract Client Classes ✅
- Created `app/client/telemetry_client.py` (TelemetryClient)
- Created `app/client/command_client.py` (CommandClient)
- MainWindowWrapper.py now only contains UI logic

#### Phase 2: Consolidate Packets ✅
- Created `app/networking/packets.py` with ALL packet classes
- Single module with clear sections (Base, Heartbeat, Commands, Telemetry, Kinect)
- Deleted 5 old packet files

#### Phase 3: Rename Hello → Heartbeat ✅
- `HelloClient` → `HeartbeatClient` (`app/client/heartbeat_client.py`)
- `HelloServer` → `HandshakeServer` (`app/server/handshake_server.py`)
- `HelloPacket` → `HeartbeatPacket`
- `HelloClientPacket` → `HeartbeatRequest`
- `HelloServerPacket` → `HeartbeatResponse`
- Backward compatibility aliases provided

#### Phase 4: Naming Conventions ✅
- `Networking/` → `networking/` (lowercase folder)
- `Misc.py` → `serialization.py`
- `LoggingWrapper.py` → `logging_wrapper.py`
- `BrickPiWrapper.py` → `brick_pi_wrapper.py`
- `CommandReceiver.py` → `command_receiver.py`
- `KinectProcess.py` → `kinect_process.py`

#### Phase 5: Dead Code Cleanup ✅
- Deleted `ControlPacket.py` (unused)
- Deleted `main_window.ui` (deprecated after GUI refactor)

#### Phase 6: KinectPacket Properties ✅
- Added property accessors (`video_frame`, `depth`, `tilt_state`, `tilt_degs`)
- Kept `get_*()` methods for backward compatibility

### Files Changed
```
app/
├── client/
│   ├── command_client.py      # NEW
│   ├── heartbeat_client.py    # NEW (was HelloClient.py)
│   ├── telemetry_client.py    # NEW
│   └── gui/
│       └── MainWindowWrapper.py  # UPDATED (extracted classes)
│
├── common/
│   ├── __init__.py            # UPDATED
│   ├── logging_wrapper.py     # NEW (was LoggingWrapper.py)
│   └── serialization.py       # NEW (was Misc.py)
│
├── networking/                 # RENAMED from Networking/
│   ├── __init__.py            # REWRITTEN
│   └── packets.py             # NEW (consolidated)
│
└── server/
    ├── brick_pi_wrapper.py    # NEW (was BrickPiWrapper.py)
    ├── command_receiver.py    # NEW (was CommandReceiver.py)
    ├── handshake_server.py    # NEW (was HelloServer.py)
    └── kinect_process.py      # NEW (was KinectProcess.py)
```

### Files Deleted
- `app/client/HelloClient.py`
- `app/server/HelloServer.py`
- `app/server/BrickPiWrapper.py`
- `app/server/CommandReceiver.py`
- `app/server/KinectProcess.py`
- `app/networking/Packet.py`
- `app/networking/HelloPacket.py`
- `app/networking/CommandPacket.py`
- `app/networking/TelemetryPacket.py`
- `app/networking/KinectPacket.py`
- `app/common/ControlPacket.py`
- `app/common/Misc.py`
- `app/common/LoggingWrapper.py`
- `app/client/gui/main_window.ui`

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking pickle compatibility (packets) | Keep same class attributes, only rename |
| Missing import updates | Grep for old names before deleting |
| Runtime errors from rename | Test each phase before proceeding |

---

## References

- Previous refactor: `doc/development/todo-gui-layout-refactor.md`
- Python naming conventions: PEP 8
- Current architecture: `doc/architecture.md`

