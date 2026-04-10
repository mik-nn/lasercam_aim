# Communication Protocol

## 1. Overview

This document defines the communication protocols between the LaserCam main application and the MeerK40t emulator plugins (Laser Emulator and Camera Emulator).

---

## 2. IPC Mechanism Selection

### 2.1 Primary: HTTP/REST + WebSocket

**Justification:**
- Simple to implement in both Python (plugins) and C++ (main app)
- Well-supported libraries available
- Easy to debug with standard tools
- Stateless commands via REST, real-time updates via WebSocket

### 2.2 Fallback: TCP Sockets

If HTTP overhead is too high for frame streaming:
- Raw TCP sockets for frame data
- JSON messages over TCP for commands
- Lower latency, more complex implementation

### 2.3 Fallback: File-based Exchange

For development/testing without running plugins:
- Position updates written to JSON files
- Frames saved as image files
- Main app polls for changes

---

## 3. Laser Emulator Protocol

### 3.1 Connection

- **Protocol**: HTTP/REST + WebSocket
- **Default Port**: 8080
- **Base URL**: `http://127.0.0.1:8080`

### 3.2 REST Endpoints

#### GET /position
Get current laser position.

**Request:**
```http
GET /position HTTP/1.1
Host: 127.0.0.1:8080
```

**Response (200 OK):**
```json
{
    "x": 100.5,
    "y": 50.2,
    "status": "idle",
    "laser_on": false,
    "timestamp": 1711900800.123
}
```

#### POST /move
Move laser to absolute position.

**Request:**
```http
POST /move HTTP/1.1
Host: 127.0.0.1:8080
Content-Type: application/json

{
    "x": 150.0,
    "y": 75.0,
    "speed": 100
}
```

**Response (200 OK):**
```json
{
    "status": "complete",
    "x": 150.0,
    "y": 75.0
}
```

**Response (400 Bad Request):**
```json
{
    "error": "invalid_coordinates",
    "message": "Position outside workspace bounds"
}
```

#### POST /move_relative
Move laser by relative amount.

**Request:**
```json
{
    "dx": 10.0,
    "dy": -5.0,
    "speed": 100
}
```

#### POST /draw
Start drawing a path.

**Request:**
```json
{
    "path": [[x1, y1], [x2, y2], [x3, y3]],
    "speed": 50
}
```

#### POST /stop
Emergency stop all movement.

**Request:**
```http
POST /stop HTTP/1.1
Host: 127.0.0.1:8080
```

**Response (200 OK):**
```json
{
    "status": "stopped",
    "x": 125.3,
    "y": 60.1
}
```

#### GET /workspace
Get workspace image.

**Response:** JPEG image binary data

#### GET /status
Get plugin status.

**Response:**
```json
{
    "workspace": {
        "width_mm": 900.0,
        "height_mm": 600.0
    },
    "laser": {
        "x": 100.5,
        "y": 50.2,
        "on": false
    },
    "paths_completed": 5,
    "uptime_seconds": 3600
}
```

### 3.3 WebSocket Updates

**Connection:** `ws://127.0.0.1:8080/ws`

**Messages:**

Position update:
```json
{
    "type": "position_update",
    "x": 100.5,
    "y": 50.2,
    "laser_on": false,
    "timestamp": 1711900800.123
}
```

Movement complete:
```json
{
    "type": "movement_complete",
    "x": 150.0,
    "y": 75.0
}
```

Error:
```json
{
    "type": "error",
    "code": "out_of_bounds",
    "message": "Target position outside workspace"
}
```

---

## 4. Camera Emulator Protocol

### 4.1 Connection

- **Protocol**: HTTP/REST + WebSocket
- **Default Port**: 8081
- **Base URL**: `http://127.0.0.1:8081`

### 4.2 REST Endpoints

#### GET /frame
Get current camera frame.

**Request:**
```http
GET /frame?format=jpeg&quality=90 HTTP/1.1
Host: 127.0.0.1:8081
```

**Response:** JPEG image binary data

#### GET /stream
Get MJPEG stream.

**Request:**
```http
GET /stream HTTP/1.1
Host: 127.0.0.1:8081
```

**Response:** `multipart/x-mixed-replace` stream

#### POST /config
Set camera configuration.

**Request:**
```json
{
    "fov_mm": [50.0, 37.5],
    "resolution": [1920, 1080],
    "fps": 30
}
```

#### GET /position
Get camera position.

**Response:**
```json
{
    "x": 100.5,
    "y": 50.2,
    "fov_mm": [50.0, 37.5],
    "resolution": [1920, 1080]
}
```

#### POST /markers
Update markers in workspace.

**Request:**
```json
{
    "markers": [
        {"x": 100.0, "y": 50.0, "angle": 45.0},
        {"x": 200.0, "y": 150.0, "angle": 225.0}
    ]
}
```

#### GET /status
Get plugin status.

**Response:**
```json
{
    "camera": {
        "x": 100.5,
        "y": 50.2,
        "fov_mm": [50.0, 37.5],
        "resolution": [1920, 1080],
        "fps": 30
    },
    "markers_count": 2,
    "frames_generated": 15000
}
```

### 4.3 WebSocket Updates

**Connection:** `ws://127.0.0.1:8081/ws`

**Messages:**

Frame ready:
```json
{
    "type": "frame_ready",
    "timestamp": 1711900800.123,
    "frame_id": 12345
}
```

Camera position update:
```json
{
    "type": "position_update",
    "x": 100.5,
    "y": 50.2
}
```

---

## 5. Data Formats

### 5.1 Coordinate System

- **Origin**: Top-left of workspace
- **X-axis**: Rightward (increasing)
- **Y-axis**: Downward (increasing)
- **Units**: Millimeters
- **Precision**: 3 decimal places (0.001mm)

### 5.2 Frame Format

- **Encoding**: JPEG (default) or PNG
- **Color Space**: BGR (OpenCV compatible)
- **Resolution**: Configurable (default 1920x1080)
- **Quality**: 1-100 (default 90)

### 5.3 Timestamp Format

- **Type**: Unix timestamp (seconds since epoch)
- **Precision**: Milliseconds (3 decimal places)

---

## 6. Timing and Synchronization

### 6.1 Update Rates

| Data Type | Update Rate | Method |
|-----------|-------------|--------|
| Laser position | 100 Hz | WebSocket |
| Camera frames | 30 FPS | MJPEG stream |
| Workspace state | On change | WebSocket |
| Status | On request | REST |

### 6.2 Synchronization

- Laser position updates include timestamps
- Camera frames include timestamps
- Main app correlates position with frames using timestamps
- Maximum acceptable latency: 50ms

### 6.3 Clock Synchronization

- Both plugins and main app use system clock
- Timestamps are in UTC
- Clock drift < 1ms acceptable

---

## 7. Error Handling

### 7.1 HTTP Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Log error, retry with corrected request |
| 404 | Not found | Check endpoint URL |
| 500 | Server error | Log error, retry after delay |
| 503 | Service unavailable | Wait and retry |

### 7.2 Connection Errors

| Error | Recovery |
|-------|----------|
| Connection refused | Retry with exponential backoff (max 5 attempts) |
| Timeout | Retry once, then report error |
| Connection lost | Attempt reconnection, notify user |
| Invalid response | Log error, request again |

### 7.3 Timeout Values

| Operation | Timeout |
|-----------|---------|
| REST request | 1000ms |
| WebSocket connect | 2000ms |
| Frame request | 500ms |
| Movement command | 5000ms |

---

## 8. Security

### 8.1 Local Development

- Bind to 127.0.0.1 only
- No authentication required
- Firewall rules restrict external access

### 8.2 Production (if needed)

- Token-based authentication
- HTTPS for REST endpoints
- WSS for WebSocket connections
- Rate limiting

---

## 9. Configuration

### 9.1 Main App Configuration

```json
{
    "communication": {
        "laser_emulator": {
            "host": "127.0.0.1",
            "port": 8080,
            "timeout_ms": 1000,
            "retries": 3
        },
        "camera_emulator": {
            "host": "127.0.0.1",
            "port": 8081,
            "timeout_ms": 500,
            "retries": 3
        }
    }
}
```

### 9.2 Plugin Configuration

See `laser-emulator-plugin.md` and `camera-emulator-plugin.md` for plugin-specific configuration.
