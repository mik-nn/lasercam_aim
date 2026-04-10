# RUIDA Protocol

## 1. Overview

RUIDA controllers use a UDP-based protocol for communication. The LaserCam application sends movement commands and receives position updates via UDP packets.

---

## 2. Connection

- **Protocol**: UDP
- **Default Port**: 50200
- **Default Host**: 192.168.1.100 (configurable)
- **Connection Type**: Stateless (each command is a separate packet)

---

## 3. Command Format

### 3.1 Movement Commands

**Move to Absolute Position:**
```
Packet structure: [header][command][x_coordinate][y_coordinate][checksum]
```

**Move by Relative Amount:**
```
Packet structure: [header][command][dx][dy][checksum]
```

### 3.2 Position Query

**Request Current Position:**
```
Packet structure: [header][query_command][checksum]
```

**Response:**
```
Packet structure: [header][response][x_position][y_position][status][checksum]
```

---

## 4. Implementation Notes

- RUIDA protocol details are proprietary and may require reverse engineering
- Initial implementation: stub with basic UDP communication
- Full implementation: packet encoding/decoding based on captured traffic
- Error handling: timeout, invalid response, connection lost

---

## 5. BaseController Interface

```python
class RuidaController(BaseController):
    def __init__(self, host: str, port: int = 50200):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    @property
    def position(self) -> tuple[float, float]:
        # Query and return current position
        pass

    def move_to(self, x_mm: float, y_mm: float) -> None:
        # Send absolute move command
        pass

    def move_by(self, dx_mm: float, dy_mm: float) -> None:
        # Send relative move command
        pass

    def release(self) -> None:
        self.socket.close()
```

---

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Protocol undocumented | Capture traffic from Ruida software, reverse engineer |
| Packet format varies by model | Support multiple packet formats, detect controller model |
| No position feedback | Implement polling with timeout, use last known position |
