# Laser Emulator Plugin

## 1. Overview

The Laser Emulator Plugin is a MeerK40t plugin that simulates the laser head, workspace, and drawing operations. It provides a visual representation of the laser workspace and exposes an API for the LaserCam main application to control and query the simulated laser.

---

## 2. Plugin Architecture

### 2.1 MeerK40t Integration

The plugin hooks into MeerK40t's event system:

```python
class LaserEmulatorPlugin:
    """
    MeerK40t plugin that emulates laser movement and drawing.
    
    Responsibilities:
    - Maintain virtual laser position
    - Render workspace with drawing paths
    - Expose HTTP/REST API for external control
    - Broadcast position updates
    """
    
    def __init__(self, kernel, path, *args):
        self.kernel = kernel
        self.channel = kernel.channel("plugin/laser_emulator")
        
        # Virtual laser state
        self.laser_x = 0.0  # mm
        self.laser_y = 0.0  # mm
        self.laser_on = False
        self.drawing_path = []
        
        # Workspace configuration
        self.workspace_width = 900.0   # mm
        self.workspace_height = 600.0  # mm
        self.background_image = None
        
        # Server for external communication
        self.server = None
        self.server_port = 8080
        
        # Register with MeerK40t
        self._register_hooks()
        
    def _register_hooks(self):
        """Subscribe to MeerK40t events."""
        @self.kernel.console("laser_move")
        def laser_move(x, y, **kwargs):
            self._on_move(x, y)
            
        @self.kernel.console("laser_draw")
        def laser_draw(path, **kwargs):
            self._on_draw(path)
            
        @self.kernel.console("laser_on")
        def laser_on(**kwargs):
            self.laser_on = True
            
        @self.kernel.console("laser_off")
        def laser_off(**kwargs):
            self.laser_on = False
```

### 2.2 Workspace Rendering

The plugin renders the workspace as a visual canvas:

```python
def render_workspace(self):
    """
    Render the current workspace state.
    
    Returns:
        numpy.ndarray: BGR image of the workspace
    """
    # Start with background image or blank canvas
    if self.background_image is not None:
        workspace = self.background_image.copy()
    else:
        workspace = np.ones(
            (int(self.workspace_height * PIXELS_PER_MM),
             int(self.workspace_width * PIXELS_PER_MM), 3),
            dtype=np.uint8
        ) * 255
    
    # Draw all completed paths
    for path in self.completed_paths:
        self._draw_path(workspace, path)
    
    # Draw current drawing path
    if self.drawing_path:
        self._draw_path(workspace, self.drawing_path, color=(255, 0, 0))
    
    # Draw laser position indicator
    self._draw_laser_indicator(workspace, self.laser_x, self.laser_y)
    
    return workspace
```

---

## 3. API Endpoints

### 3.1 HTTP/REST API

The plugin exposes the following endpoints:

#### GET /position
Returns the current laser position.

**Response:**
```json
{
    "x": 100.5,
    "y": 50.2,
    "status": "idle",
    "laser_on": false
}
```

#### POST /move
Move the laser to an absolute position.

**Request:**
```json
{
    "x": 150.0,
    "y": 75.0,
    "speed": 100
}
```

**Response:**
```json
{
    "status": "complete",
    "x": 150.0,
    "y": 75.0
}
```

#### POST /move_relative
Move the laser by a relative amount.

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
    "path": [[x1, y1], [x2, y2], [x3, y3], ...],
    "speed": 50
}
```

#### POST /stop
Stop all movement immediately.

**Response:**
```json
{
    "status": "stopped",
    "x": 125.3,
    "y": 60.1
}
```

#### GET /workspace
Get the current workspace image.

**Response:** JPEG image of the workspace

#### GET /status
Get plugin status and configuration.

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
    "paths_completed": 5
}
```

---

## 4. Configuration

### 4.1 Plugin Configuration

```json
{
    "laser_emulator": {
        "workspace": {
            "width_mm": 900.0,
            "height_mm": 600.0,
            "background_image": "workspace.png",
            "pixels_per_mm": 10
        },
        "laser": {
            "max_speed_mm_per_s": 200,
            "acceleration_mm_per_s2": 1000,
            "indicator_size_mm": 5
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8080
        }
    }
}
```

### 4.2 Coordinate System

- Origin: Top-left of workspace
- X-axis: Rightward (increasing)
- Y-axis: Downward (increasing)
- Units: Millimeters

---

## 5. Movement Simulation

### 5.1 Linear Interpolation

Movement is simulated using linear interpolation:

```python
def _simulate_move(self, target_x, target_y, speed):
    """
    Simulate laser movement to target position.
    
    Args:
        target_x: Target X position (mm)
        target_y: Target Y position (mm)
        speed: Movement speed (mm/s)
    """
    dx = target_x - self.laser_x
    dy = target_y - self.laser_y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance == 0:
        return
    
    duration = distance / speed
    steps = int(duration * UPDATES_PER_SECOND)
    
    for i in range(steps + 1):
        t = i / steps
        self.laser_x = self.laser_x + dx * t
        self.laser_y = self.laser_y + dy * t
        
        # Broadcast position update
        self._broadcast_position()
        
        # Small delay for real-time simulation
        time.sleep(1.0 / UPDATES_PER_SECOND)
```

### 5.2 Drawing Simulation

When drawing, the plugin:
1. Receives a path (list of points)
2. Moves the laser along the path
3. Records the path for rendering
4. Updates the workspace image

---

## 6. Position Broadcasting

The plugin broadcasts position updates via:

1. **WebSocket**: Real-time updates to connected clients
2. **HTTP Polling**: Clients can poll GET /position
3. **File-based**: Write position to a shared file (fallback)

```python
def _broadcast_position(self):
    """Broadcast current laser position to all clients."""
    update = {
        "type": "position_update",
        "x": self.laser_x,
        "y": self.laser_y,
        "laser_on": self.laser_on,
        "timestamp": time.time()
    }
    
    # Send to WebSocket clients
    for client in self.websocket_clients:
        client.send(json.dumps(update))
    
    # Update position file (fallback)
    with open(self.position_file, 'w') as f:
        json.dump(update, f)
```

---

## 7. Error Handling

| Error | Response |
|-------|----------|
| Invalid coordinates | Return error, don't move |
| Movement interrupted | Stop at current position, report status |
| Server port in use | Try next port, log warning |
| Workspace image load failed | Use blank canvas |

---

## 8. Testing

### 8.1 Unit Tests
- Position tracking accuracy
- Movement simulation correctness
- Path rendering accuracy
- API endpoint responses

### 8.2 Integration Tests
- Communication with LaserCam main app
- Synchronization with camera emulator
- End-to-end workflow

### 8.3 Performance Tests
- Movement simulation frame rate
- API response latency
- Workspace rendering performance
