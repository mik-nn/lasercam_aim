# GRBL Protocol

## 1. Overview

GRBL controllers use a serial-based protocol for communication. The LaserCam application sends G-code commands and receives position updates via serial port.

---

## 2. Connection

- **Protocol**: Serial (RS-232/USB)
- **Default Baud Rate**: 115200
- **Default Port**: COM3 (Windows) / /dev/ttyUSB0 (Linux)
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None

---

## 3. Command Format

### 3.1 Movement Commands

**Move to Absolute Position (G90 mode):**
```
G0 X{x:.3f} Y{y:.3f}
```

**Move by Relative Amount (G91 mode):**
```
G91
G0 X{dx:.3f} Y{dy:.3f}
G90  # Return to absolute mode
```

### 3.2 Position Query

**Request Current Position:**
```
?
```

**Response (Grbl 1.1):**
```
<Idle|MPos:100.000,50.000,0.000|FS:0,0>
```

**Response (Grbl 0.9):**
```
<Idle,MPos:100.000,50.000,0.000>
```

---

## 4. Implementation Notes

- GRBL uses standard G-code commands
- Position is reported in machine coordinates (MPos) or work coordinates (WPos)
- Status reports include machine state (Idle, Run, Hold, etc.)
- Error responses start with `error:` or `alarm:`

---

## 5. BaseController Interface

```python
class GRBLController(BaseController):
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = serial.Serial(port, baudrate, timeout=1)

    @property
    def position(self) -> tuple[float, float]:
        # Send '?' query and parse response
        pass

    def move_to(self, x_mm: float, y_mm: float) -> None:
        # Send G0 X Y command in absolute mode
        pass

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        # Send relative move command
        pass

    def release(self) -> None:
        self.serial.close()
```

---

## 6. Error Handling

| Error | Response |
|-------|----------|
| Serial timeout | Retry up to 3 times, then report error |
| Invalid response | Log warning, use last known position |
| GRBL alarm | Stop all movement, report alarm code |
| Connection lost | Attempt reconnection, notify user |

---

## 7. Configuration

```json
{
  "grbl": {
    "port": "COM3",
    "baudrate": 115200,
    "timeout_ms": 1000,
    "retries": 3
  }
}
```
