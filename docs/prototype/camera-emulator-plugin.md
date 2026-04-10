# Camera Emulator Plugin

## 1. Overview

The Camera Emulator Plugin is a MeerK40t plugin that simulates a camera viewing the workspace. It generates camera frames based on the current workspace state and the simulated camera position, rendering markers and other elements within the camera's field of view.

---

## 2. Plugin Architecture

### 2.1 MeerK40t Integration

```python
class CameraEmulatorPlugin:
    """
    MeerK40t plugin that emulates a camera viewing the workspace.
    
    Responsibilities:
    - Simulate camera field of view
    - Generate frames from workspace state
    - Render markers in camera view
    - Stream frames to LaserCam main app
    """
    
    def __init__(self, kernel, path, *args):
        self.kernel = kernel
        self.channel = kernel.channel("plugin/camera_emulator")
        
        # Camera configuration
        self.camera_x = 0.0  # mm - camera center position
        self.camera_y = 0.0  # mm
        self.fov_width_mm = 50.0   # Field of view width
        self.fov_height_mm = 37.5  # Field of view height
        self.resolution = (1920, 1080)  # Output frame resolution
        self.fps = 30
        
        # Workspace reference (shared with laser emulator)
        self.workspace = None
        self.workspace_width_mm = 900.0
        self.workspace_height_mm = 600.0
        self.pixels_per_mm = 10
        
        # Markers to render
        self.markers = []  # List of (x, y, angle) tuples
        
        # Server for frame streaming
        self.server = None
        self.server_port = 8081
        
        # Register with MeerK40t
        self._register_hooks()
        
    def _register_hooks(self):
        """Subscribe to MeerK40t events."""
        @self.kernel.console("camera_move")
        def camera_move(x, y, **kwargs):
            self.camera_x = x
            self.camera_y = y
            
        @self.kernel.console("camera_config")
        def camera_config(fov_w, fov_h, resolution, **kwargs):
            self.fov_width_mm = fov_w
            self.fov_height_mm = fov_h
            self.resolution = resolution
```

### 2.2 Frame Generation

The plugin generates frames by cropping and rendering the workspace:

```python
def generate_frame(self):
    """
    Generate a camera frame from the current workspace state.
    
    Returns:
        numpy.ndarray: BGR image representing the camera view
    """
    if self.workspace is None:
        return self._generate_blank_frame()
    
    # Calculate crop region in workspace pixels
    crop_w_px = int(self.fov_width_mm * self.pixels_per_mm)
    crop_h_px = int(self.fov_height_mm * self.pixels_per_mm)
    
    cam_x_px = int(self.camera_x * self.pixels_per_mm)
    cam_y_px = int(self.camera_y * self.pixels_per_mm)
    
    # Calculate crop boundaries
    x1 = max(0, cam_x_px - crop_w_px // 2)
    y1 = max(0, cam_y_px - crop_h_px // 2)
    x2 = min(self.workspace.shape[1], cam_x_px + crop_w_px // 2)
    y2 = min(self.workspace.shape[0], cam_y_px + crop_h_px // 2)
    
    # Crop the workspace
    crop = self.workspace[y1:y2, x1:x2]
    
    if crop.size == 0:
        return self._generate_blank_frame()
    
    # Resize to camera resolution
    frame = cv2.resize(crop, self.resolution, interpolation=cv2.INTER_LINEAR)
    
    # Render markers in the frame
    frame = self._render_markers(frame, x1, y1, self.pixels_per_mm)
    
    return frame
```

---

## 3. Marker Rendering

The plugin renders the new unified circle markers in the camera view:

```python
def _render_markers(self, frame, crop_x, crop_y, ppm):
    """
    Render markers in the camera frame.
    
    Args:
        frame: Camera frame image
        crop_x: X offset of crop in workspace pixels
        crop_y: Y offset of crop in workspace pixels
        ppm: Pixels per mm
    
    Returns:
        numpy.ndarray: Frame with markers rendered
    """
    for marker in self.markers:
        mx, my, angle = marker
        
        # Convert marker position to frame coordinates
        fx = int((mx * ppm - crop_x) * (frame.shape[1] / (self.fov_width_mm * ppm)))
        fy = int((my * ppm - crop_y) * (frame.shape[0] / (self.fov_height_mm * ppm)))
        
        # Check if marker is within frame
        if not (0 <= fx < frame.shape[1] and 0 <= fy < frame.shape[0]):
            continue
        
        # Draw solid black circle
        radius_px = int(5.0 * ppm / 2)  # 5mm diameter
        cv2.circle(frame, (fx, fy), radius_px, (0, 0, 0), -1)
        
        # Draw white direction line
        line_len = int(2.0 * ppm)  # 2mm length
        line_w = int(0.7 * ppm)    # 0.7mm width
        angle_rad = math.radians(angle)
        
        # Calculate line endpoints
        start_x = fx
        start_y = fy
        end_x = int(fx + line_len * math.cos(angle_rad))
        end_y = int(fy + line_len * math.sin(angle_rad))
        
        # Draw line as thick line
        cv2.line(frame, (start_x, start_y), (end_x, end_y), 
                 (255, 255, 255), line_w)
    
    return frame
```

---

## 4. API Endpoints

### 4.1 HTTP/REST API

#### GET /frame
Get the current camera frame.

**Response:** JPEG image

**Query Parameters:**
- `format`: "jpeg" (default) or "png"
- `quality`: 1-100 (default 90)

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
Get current camera position.

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
Add or update markers in the workspace.

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
    "markers_count": 2
}
```

---

## 5. Frame Streaming

### 5.1 Streaming Modes

1. **HTTP Multipart**: MJPEG stream via HTTP
2. **WebSocket**: Real-time frame streaming
3. **Polling**: Client requests frames on demand

### 5.2 MJPEG Stream

```python
def _serve_mjpeg_stream(self, request):
    """Serve camera frames as MJPEG stream."""
    def frame_generator():
        while True:
            frame = self.generate_frame()
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   jpeg.tobytes() + b'\r\n')
            
            time.sleep(1.0 / self.fps)
    
    return Response(frame_generator(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')
```

---

## 6. Configuration

```json
{
    "camera_emulator": {
        "camera": {
            "fov_mm": [50.0, 37.5],
            "resolution": [1920, 1080],
            "fps": 30,
            "initial_position": [100.0, 50.0]
        },
        "workspace": {
            "width_mm": 900.0,
            "height_mm": 600.0,
            "pixels_per_mm": 10
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8081
        },
        "markers": [
            {"x": 809.2, "y": 480.3, "angle": 157.0},
            {"x": 751.0, "y": 506.0, "angle": 337.0}
        ]
    }
}
```

---

## 7. Synchronization with Laser Emulator

The camera emulator must stay synchronized with the laser emulator:

### 7.1 Shared State
- Both plugins access the same workspace image
- Camera position updates when laser moves (if camera is mounted on gantry)
- Markers are shared between plugins

### 7.2 Synchronization Mechanism

```python
def _on_workspace_update(self, workspace_data):
    """Update when workspace changes."""
    self.workspace = workspace_data['image']
    self.markers = workspace_data['markers']
    
def _on_laser_position_update(self, position):
    """Update camera position if mounted on gantry."""
    if self.camera_mounted_on_gantry:
        self.camera_x = position['x'] + self.camera_offset_x
        self.camera_y = position['y'] + self.camera_offset_y
```

---

## 8. Error Handling

| Error | Response |
|-------|----------|
| Workspace not loaded | Return blank frame |
| Invalid configuration | Use defaults, log warning |
| Frame generation failed | Return last valid frame |
| Server port in use | Try next port, log warning |

---

## 9. Testing

### 9.1 Unit Tests
- Frame generation correctness
- Marker rendering accuracy
- Configuration handling
- Crop and resize operations

### 9.2 Integration Tests
- Communication with LaserCam main app
- Synchronization with laser emulator
- Frame streaming performance

### 9.3 Performance Tests
- Frame generation latency
- Streaming frame rate
- Memory usage
