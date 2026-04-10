# mvp/plugins/meerk40t_plugin/camera_emulator_plugin.py
"""
Camera Emulator Plugin for MeerK40t.

Starts an HTTP server on port 8081 that provides:
- GET /health - Health check
- GET /position - Current camera position
- GET /frame - Camera frame as JPEG
- POST /position - Update camera position {"x": mm, "y": mm}

AICODE-NOTE: This plugin starts the HTTP server during the 'boot' lifecycle,
so it's available as soon as MeerK40t finishes loading.
"""
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

import cv2


# Module-level state
_state = {
    "camera_x": 0.0,
    "camera_y": 0.0,
    "fov_mm": (50.0, 37.5),
    "resolution": (1920, 1080),
    "fps": 30,
    "workspace_pixels_per_mm": 7.874,
    "workspace_image": None,
    "lock": threading.Lock(),
}

_server = None
_thread = None


def plugin(kernel, lifecycle):
    """MeerK40t plugin entry point.

    Called multiple times with different lifecycle values:
    register -> boot -> ready -> premain -> postmain -> shutdown
    """
    if lifecycle == "register":
        # Register console commands early
        @kernel.console_command("camera_position", help="Get current camera position")
        def get_position_cmd(channel=None, **kw):
            with _state["lock"]:
                x, y = _state["camera_x"], _state["camera_y"]
            if channel:
                channel(f"Camera position: ({x:.2f}, {y:.2f}) mm")

        @kernel.console_command("camera_frame", help="Save current camera frame to file")
        def save_frame_cmd(channel=None, **kw):
            frame = _render_frame()
            if frame is not None:
                cv2.imwrite("camera_frame.png", frame)
                if channel:
                    channel("Frame saved to camera_frame.png")
            else:
                if channel:
                    channel("No workspace image loaded")

    elif lifecycle in ("boot", "ready"):
        # Start HTTP server during boot (after commands registered)
        _start_server()

    elif lifecycle == "shutdown":
        _stop_server()


def _start_server():
    global _server, _thread
    if _server:
        return

    handler = _make_handler()
    _server = HTTPServer(("127.0.0.1", 8081), handler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print("[LaserCam] Camera Emulator HTTP server started on http://127.0.0.1:8081")


def _stop_server():
    global _server, _thread
    if _server:
        _server.shutdown()
        _server = None
        _thread = None
        print("[LaserCam] Camera Emulator HTTP server stopped")


def _render_frame():
    """Render camera view from workspace image."""
    with _state["lock"]:
        if _state["workspace_image"] is None:
            return None

        wa = _state["workspace_image"]
        wa_h, wa_w = wa.shape[:2]

        cam_x_px = int(_state["camera_x"] * _state["workspace_pixels_per_mm"])
        cam_y_px = int(_state["camera_y"] * _state["workspace_pixels_per_mm"])

        crop_w = int(_state["fov_mm"][0] * _state["workspace_pixels_per_mm"])
        crop_h = int(_state["fov_mm"][1] * _state["workspace_pixels_per_mm"])

        start_x = max(0, cam_x_px - crop_w // 2)
        end_x = min(wa_w, cam_x_px + crop_w // 2)
        start_y = max(0, cam_y_px - crop_h // 2)
        end_y = min(wa_h, cam_y_px + crop_h // 2)

        crop = wa[start_y:end_y, start_x:end_x]
        if crop.size == 0:
            return None

        out_w, out_h = _state["resolution"]
        return cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)


def _make_handler():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send_json(self, data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def _send_image(self, frame):
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(buf)))
            self.end_headers()
            self.wfile.write(buf.tobytes())

        def do_GET(self):
            if self.path == "/frame":
                frame = _render_frame()
                if frame is not None:
                    self._send_image(frame)
                else:
                    self._send_json({"error": "No frame available"}, 503)
            elif self.path == "/position":
                with _state["lock"]:
                    self._send_json({
                        "x": _state["camera_x"],
                        "y": _state["camera_y"],
                        "fov_mm": list(_state["fov_mm"]),
                        "resolution": list(_state["resolution"]),
                    })
            elif self.path == "/health":
                self._send_json({"status": "ok"})
            else:
                self._send_json({"error": "Not found"}, 404)

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON"}, 400)
                return

            if self.path == "/position":
                x = data.get("x")
                y = data.get("y")
                if x is not None and y is not None:
                    with _state["lock"]:
                        _state["camera_x"] = float(x)
                        _state["camera_y"] = float(y)
                    self._send_json({"status": "updated"})
                else:
                    self._send_json({"error": "Missing x or y"}, 400)
            else:
                self._send_json({"error": "Not found"}, 404)

    return Handler
