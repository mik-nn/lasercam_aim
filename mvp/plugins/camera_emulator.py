# mvp/plugins/camera_emulator.py
"""
Camera Emulator Plugin for MeerK40t integration.

Provides an HTTP API for the LaserCam main application to:
- Get current camera frame (JPEG/PNG)
- Configure camera parameters (FOV, resolution)
- Query camera position

AICODE-NOTE: This is a standalone emulation server that mimics the
behaviour of a MeerK40t Camera Emulator plugin. It renders camera FOV
from a shared workspace state.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import cv2
import numpy as np


class CameraState:
    """Shared camera state for the camera emulator."""

    def __init__(
        self,
        fov_mm: tuple[float, float] = (50.0, 37.5),
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 30,
    ):
        self.fov_mm = fov_mm
        self.resolution = resolution
        self.fps = fps
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.workspace_image: Optional[np.ndarray] = None
        self.workspace_pixels_per_mm: float = 7.874
        self._lock = threading.Lock()

    def set_position(self, x: float, y: float) -> None:
        with self._lock:
            self.camera_x = x
            self.camera_y = y

    def get_position(self) -> dict:
        with self._lock:
            return {
                "x": self.camera_x,
                "y": self.camera_y,
                "fov_mm": list(self.fov_mm),
                "resolution": list(self.resolution),
            }

    def get_config(self) -> dict:
        with self._lock:
            return {
                "fov_mm": list(self.fov_mm),
                "resolution": list(self.resolution),
                "fps": self.fps,
            }

    def set_config(self, fov_mm=None, resolution=None, fps=None) -> None:
        with self._lock:
            if fov_mm is not None:
                self.fov_mm = tuple(fov_mm)
            if resolution is not None:
                self.resolution = tuple(resolution)
            if fps is not None:
                self.fps = fps

    def render_frame(self) -> Optional[np.ndarray]:
        """Render the current camera view from workspace image."""
        with self._lock:
            if self.workspace_image is None:
                return None

            wa = self.workspace_image
            wa_h, wa_w = wa.shape[:2]

            cam_x_px = int(self.camera_x * self.workspace_pixels_per_mm)
            cam_y_px = int(self.camera_y * self.workspace_pixels_per_mm)

            crop_w = int(self.fov_mm[0] * self.workspace_pixels_per_mm)
            crop_h = int(self.fov_mm[1] * self.workspace_pixels_per_mm)

            start_x = max(0, cam_x_px - crop_w // 2)
            end_x = min(wa_w, cam_x_px + crop_w // 2)
            start_y = max(0, cam_y_px - crop_h // 2)
            end_y = min(wa_h, cam_y_px + crop_h // 2)

            crop = wa[start_y:end_y, start_x:end_x]
            if crop.size == 0:
                return None

            out_w, out_h = self.resolution
            return cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)


class CameraEmulatorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Camera Emulator."""

    camera_state: CameraState = None  # type: ignore

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_image(self, frame: np.ndarray) -> None:
        """Send a JPEG frame as response."""
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(buf)))
        self.end_headers()
        self.wfile.write(buf.tobytes())

    def do_GET(self) -> None:
        if self.path == "/frame":
            frame = self.camera_state.render_frame()
            if frame is not None:
                self._send_image(frame)
            else:
                self._send_json({"error": "No frame available"}, 503)

        elif self.path == "/position":
            self._send_json(self.camera_state.get_position())

        elif self.path == "/config":
            self._send_json(self.camera_state.get_config())

        elif self.path == "/health":
            self._send_json({"status": "ok"})

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return

        if self.path == "/config":
            self.camera_state.set_config(
                fov_mm=data.get("fov_mm"),
                resolution=data.get("resolution"),
                fps=data.get("fps"),
            )
            self._send_json({"status": "updated"})

        elif self.path == "/position":
            x = data.get("x")
            y = data.get("y")
            if x is not None and y is not None:
                self.camera_state.set_position(float(x), float(y))
                self._send_json({"status": "updated"})
            else:
                self._send_json({"error": "Missing x or y"}, 400)

        else:
            self._send_json({"error": "Not found"}, 404)


class CameraEmulatorServer:
    """
    HTTP server for the Camera Emulator plugin.

    Can be run standalone or integrated into MeerK40t as a plugin.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8081,
        camera_state: Optional[CameraState] = None,
    ):
        self.host = host
        self.port = port
        self.camera_state = camera_state or CameraState()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def load_workspace(self, image_path: str) -> None:
        """Load workspace image for rendering camera frames."""
        img = cv2.imread(image_path)
        if img is not None:
            self.camera_state.workspace_image = img
            print(f"Workspace image loaded: {image_path}")
        else:
            print(f"Warning: Could not load workspace image: {image_path}")

    def start(self) -> None:
        """Start the HTTP server in a background thread."""
        CameraEmulatorHandler.camera_state = self.camera_state
        self._server = HTTPServer((self.host, self.port), CameraEmulatorHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"Camera Emulator started at http://{self.host}:{self.port}")

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server:
            self._server.shutdown()
            print("Camera Emulator stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Camera Emulator Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8081, help="Bind port")
    parser.add_argument(
        "--workspace", default="Workspace90x60cm+sample.png",
        help="Workspace image path",
    )
    args = parser.parse_args()

    server = CameraEmulatorServer(host=args.host, port=args.port)
    server.load_workspace(args.workspace)
    try:
        server.start()
        print("Press Ctrl+C to stop")
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
