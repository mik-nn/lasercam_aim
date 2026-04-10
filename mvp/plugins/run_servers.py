# mvp/plugins/run_servers.py
"""
Run both LaserCam HTTP servers in a single process.
This is the recommended way to start the servers.

Usage:
    python mvp/plugins/run_servers.py [--laser-port 8080] [--camera-port 8081]
"""
import argparse
import sys
import time

import numpy as np

sys.path.insert(0, ".")

from mvp.plugins.laser_emulator import LaserEmulatorServer  # noqa: E402
from mvp.plugins.camera_emulator import CameraEmulatorServer  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="LaserCam HTTP Servers")
    parser.add_argument("--laser-port", type=int, default=8080)
    parser.add_argument("--camera-port", type=int, default=8081)
    args = parser.parse_args()

    print("=" * 50)
    print("  LaserCam HTTP Servers")
    print("=" * 50)
    print()

    # Laser Emulator
    laser = LaserEmulatorServer(port=args.laser_port)
    laser.start()

    # Camera Emulator
    camera = CameraEmulatorServer(port=args.camera_port)
    camera.camera_state.workspace_image = np.ones(
        (1000, 1000, 3), dtype=np.uint8
    ) * 255
    camera.camera_state.workspace_pixels_per_mm = 10.0
    camera.start()

    print()
    print(f"  Laser:  http://127.0.0.1:{args.laser_port}")
    print(f"  Camera: http://127.0.0.1:{args.camera_port}")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 50)
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        laser.stop()
        camera.stop()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
