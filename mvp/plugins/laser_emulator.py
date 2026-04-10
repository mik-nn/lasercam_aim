# mvp/plugins/laser_emulator.py
"""
Laser Emulator Plugin for MeerK40t integration.

Provides an HTTP API for the LaserCam main application to:
- Get/set laser position
- Move the laser head
- Query workspace state
- Simulate drawing paths

AICODE-NOTE: This is a standalone emulation server that mimics the
behaviour of a MeerK40t Laser Emulator plugin. It can run independently
or be embedded as a MeerK40t plugin module.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional


class WorkspaceState:
    """Shared workspace state for the laser emulator."""

    def __init__(
        self,
        width_mm: float = 900.0,
        height_mm: float = 600.0,
        speed_mm_per_s: float = 100.0,
        acceleration_mm_per_s2: float = 500.0,
    ):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.speed_mm_per_s = speed_mm_per_s
        self.acceleration_mm_per_s2 = acceleration_mm_per_s2
        self.laser_x = 0.0
        self.laser_y = 0.0
        self.is_moving = False
        self.draw_paths: list[list[tuple[float, float]]] = []
        self._lock = threading.Lock()

    def get_position(self) -> dict:
        with self._lock:
            return {
                "x": self.laser_x,
                "y": self.laser_y,
                "status": "moving" if self.is_moving else "idle",
            }

    def move_to(self, x: float, y: float) -> None:
        with self._lock:
            self.laser_x = max(0, min(x, self.width_mm))
            self.laser_y = max(0, min(y, self.height_mm))

    def add_draw_path(self, path: list[tuple[float, float]]) -> None:
        with self._lock:
            self.draw_paths.append([(float(x), float(y)) for x, y in path])

    def get_workspace(self) -> dict:
        with self._lock:
            return {
                "width": self.width_mm,
                "height": self.height_mm,
                "laser_x": self.laser_x,
                "laser_y": self.laser_y,
                "draw_paths": self.draw_paths,
            }


class LaserEmulatorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Laser Emulator."""

    workspace: WorkspaceState = None  # type: ignore

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self) -> None:
        if self.path == "/position":
            self._send_json(self.workspace.get_position())
        elif self.path == "/workspace":
            self._send_json(self.workspace.get_workspace())
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

        if self.path == "/move":
            x = data.get("x")
            y = data.get("y")
            if x is None or y is None:
                self._send_json({"error": "Missing x or y"}, 400)
                return
            self.workspace.move_to(float(x), float(y))
            self._send_json({"status": "complete"})

        elif self.path == "/draw":
            path = data.get("path", [])
            if not path:
                self._send_json({"error": "Missing path"}, 400)
                return
            parsed_path = [(float(p[0]), float(p[1])) for p in path]
            self.workspace.add_draw_path(parsed_path)
            # Move laser to end of path
            if parsed_path:
                self.workspace.move_to(parsed_path[-1][0], parsed_path[-1][1])
            self._send_json({"status": "complete"})

        elif self.path == "/stop":
            self.workspace.is_moving = False
            self._send_json({"status": "stopped"})

        else:
            self._send_json({"error": "Not found"}, 404)


class LaserEmulatorServer:
    """
    HTTP server for the Laser Emulator plugin.

    Can be run standalone or integrated into MeerK40t as a plugin.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        workspace: Optional[WorkspaceState] = None,
    ):
        self.host = host
        self.port = port
        self.workspace = workspace or WorkspaceState()
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a background thread."""
        LaserEmulatorHandler.workspace = self.workspace
        self._server = HTTPServer((self.host, self.port), LaserEmulatorHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"Laser Emulator started at http://{self.host}:{self.port}")

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server:
            self._server.shutdown()
            print("Laser Emulator stopped")

    def get_position(self) -> tuple[float, float]:
        """Get current laser position."""
        return self.workspace.laser_x, self.workspace.laser_y

    def move_to(self, x: float, y: float) -> None:
        """Move laser to position."""
        self.workspace.move_to(x, y)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Laser Emulator Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    args = parser.parse_args()

    server = LaserEmulatorServer(host=args.host, port=args.port)
    try:
        server.start()
        print("Press Ctrl+C to stop")
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
