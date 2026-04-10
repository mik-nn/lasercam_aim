# mvp/plugins/meerk40t_plugin/laser_emulator_plugin.py
"""
Laser Emulator Plugin for MeerK40t.

Starts an HTTP server on port 8080 that provides:
- GET /health - Health check
- GET /position - Current laser position
- GET /workspace - Workspace state
- POST /move - Move laser to position {"x": mm, "y": mm}
- POST /stop - Stop movement

AICODE-NOTE: This plugin starts the HTTP server during the 'boot' lifecycle,
so it's available as soon as MeerK40t finishes loading.
"""
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


# Module-level state (shared across plugin instances)
_state = {
    "laser_x": 0.0,
    "laser_y": 0.0,
    "is_moving": False,
    "workspace_width_mm": 900.0,
    "workspace_height_mm": 600.0,
    "draw_paths": [],
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
        @kernel.console_command("laser_position", help="Get current laser position")
        def get_position_cmd(channel=None, **kw):
            with _state["lock"]:
                x, y = _state["laser_x"], _state["laser_y"]
            if channel:
                channel(f"Laser position: ({x:.2f}, {y:.2f}) mm")

        @kernel.console_argument("x", type=float)
        @kernel.console_argument("y", type=float)
        @kernel.console_command("laser_move", help="Move laser to position (mm)")
        def move_to_cmd(channel=None, x=None, y=None, **kw):
            if x is not None and y is not None:
                with _state["lock"]:
                    _state["laser_x"] = max(0, min(x, _state["workspace_width_mm"]))
                    _state["laser_y"] = max(0, min(y, _state["workspace_height_mm"]))
                if channel:
                    channel(f"Moved to ({x:.2f}, {y:.2f})")

        @kernel.console_command("laser_home", help="Move laser to home position")
        def laser_home_cmd(channel=None, **kw):
            with _state["lock"]:
                _state["laser_x"] = 0.0
                _state["laser_y"] = 0.0
            if channel:
                channel("Laser homed")

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
    _server = HTTPServer(("127.0.0.1", 8080), handler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    print("[LaserCam] Laser Emulator HTTP server started on http://127.0.0.1:8080")


def _stop_server():
    global _server, _thread
    if _server:
        _server.shutdown()
        _server = None
        _thread = None
        print("[LaserCam] Laser Emulator HTTP server stopped")


def _make_handler():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send_json(self, data, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def do_GET(self):
            if self.path == "/position":
                with _state["lock"]:
                    self._send_json({
                        "x": _state["laser_x"],
                        "y": _state["laser_y"],
                        "status": "moving" if _state["is_moving"] else "idle",
                    })
            elif self.path == "/workspace":
                with _state["lock"]:
                    self._send_json({
                        "width": _state["workspace_width_mm"],
                        "height": _state["workspace_height_mm"],
                        "laser_x": _state["laser_x"],
                        "laser_y": _state["laser_y"],
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

            if self.path == "/move":
                x = data.get("x")
                y = data.get("y")
                if x is not None and y is not None:
                    with _state["lock"]:
                        _state["laser_x"] = max(0, min(float(x), _state["workspace_width_mm"]))
                        _state["laser_y"] = max(0, min(float(y), _state["workspace_height_mm"]))
                    self._send_json({"status": "complete"})
                else:
                    self._send_json({"error": "Missing x or y"}, 400)
            elif self.path == "/stop":
                with _state["lock"]:
                    _state["is_moving"] = False
                self._send_json({"status": "stopped"})
            else:
                self._send_json({"error": "Not found"}, 404)

    return Handler
