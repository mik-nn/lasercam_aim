# LaserCam Alignment Assistant

This project provides a marker-based alignment assistant for laser cutters. It uses a camera to detect printed markers on the work material, automatically moves the laser to the precise center of these markers, and assists with two-point alignment for accurate cuts on pre-printed designs.

## Features

- **Real-time Camera Preview**: Shows a live feed from the camera (real or emulated).
- **Automatic Marker Detection**: Detects solid circle markers with direction lines using OpenCV.
- **Automated Laser Positioning**: Moves the laser to the exact center of detected markers.
- **Directional Navigation**: Automatically navigates from M1 to M2 using the detected direction line.
- **Two-Point Alignment**: Guides the user through a simple two-marker alignment process.
- **Simulator Mode**: Built-in workspace simulator with camera emulation for development without hardware.
- **MeerK40t Plugin Support**: Laser and Camera Emulator plugins for full workflow emulation.
- **Controller Abstraction**: Supports GRBL (serial) and RUIDA (UDP) laser controllers.
- **Calibration System**: Laser-camera offset calibration with change detection.

## Workflow

1. **Print Artwork**: Print your design with two alignment markers (M1 and M2).
2. **Position Material**: Place the printed material on the laser bed.
3. **First Marker**: Manually move the camera/gantry so M1 is visible in the camera view.
4. **Detect & Align**: The tool detects M1 and moves the laser to its center.
5. **Confirm M1**: User confirms the marker position.
6. **Navigate to M2**: The tool automatically moves toward M2 using the direction line from M1.
7. **Confirm M2**: User confirms the second marker position.
8. **Complete**: Both alignment points are registered.

## Architecture

The project is developed in two stages:

1. **MVP (Python)**: Rapid prototyping with MeerK40t emulation, OpenCV-based marker detection, and Tkinter UI.
2. **Final Tool (C++/Qt)**: Production-ready standalone application with identical external behaviour.

Both share the same detection semantics, coordinate mapping, and state machine.

## Technology Stack

| Component | MVP (Python) | Final Tool (C++/Qt) |
|---|---|---|
| **Language** | Python 3 | C++17 |
| **UI** | Tkinter | Qt (5/6) |
| **Image Processing** | OpenCV | OpenCV |
| **Camera** | DirectShow via OpenCV | DirectShow/Media Foundation |
| **Controllers** | GRBL (pyserial), RUIDA (UDP) | GRBL (QSerialPort), RUIDA (QUdpSocket) |
| **Emulation** | MeerK40t plugins (HTTP API) | Standalone simulator |

## Project Structure

```
/
├── docs/                  # Project documentation
├── mvp/                   # Python MVP source code
│   ├── app.py             # Application orchestration
│   ├── ui.py              # Tkinter UI with state machine
│   ├── camera.py          # Real camera interface
│   ├── camera_simulator.py # Camera simulator
│   ├── simulator.py       # Motion simulator
│   ├── controller.py      # BaseController + GRBL/RUIDA/Simulated
│   ├── recognizer.py      # Marker detection (circle + line)
│   ├── config.py          # Configuration management
│   ├── bridge.py          # LightBurn bridge (stub)
│   ├── plugins/           # MeerK40t emulation plugins
│   │   ├── laser_emulator.py    # HTTP API for laser position/movement
│   │   └── camera_emulator.py   # HTTP API for camera frames
│   └── tests/             # 76 unit/integration tests
├── final/                 # C++/Qt final tool (skeleton)
│   ├── CMakeLists.txt
│   ├── src/
│   │   ├── core/          # BaseController, CalibrationManager, AppState
│   │   ├── camera/        # CameraInterface
│   │   ├── recognizer/    # MarkerRecognizer (C++ port)
│   │   ├── controllers/   # GRBLController, RuidaController
│   │   └── ui/            # MainWindow, CameraView
│   └── tests/             # Google Test suite
├── markers/               # Marker templates and reference images
├── plans/                 # Agent plans
└── generate_marker.py     # Adobe Illustrator marker generation script
```

## Running the MVP

```bash
# Install dependencies
pip install -r requirements.txt

# Run the simulator
python -m mvp.app

# Run tests
pytest mvp/tests/ -v

# Type check
python -m pyright mvp/

# Lint
python -m flake8 mvp/
```

## MeerK40t Plugins

The Laser and Camera Emulator plugins can run as standalone HTTP servers:

```bash
# Laser Emulator (default port 8080)
python -m mvp.plugins.laser_emulator

# Camera Emulator (default port 8081)
python -m mvp.plugins.camera_emulator --workspace Workspace90x60cm+sample.png
```

API endpoints:
- `GET /position` — Current position
- `POST /move` — Move to position `{"x": 100, "y": 50}`
- `GET /frame` — Camera frame (JPEG)
- `POST /config` — Configure camera parameters

## Core Modules

- **Camera Module**: Captures video or provides simulated frames.
- **Marker Recognizer**: Detects solid circle markers with white direction lines.
- **Controller Layer**: Abstracts GRBL (serial), RUIDA (UDP), and simulated movement.
- **Calibration Manager**: Manages laser-camera offset with validation.
- **MeerK40t Plugins**: HTTP-based emulation for laser and camera.
- **UI Layer**: Tkinter (MVP) / Qt (final) with state machine and overlays.

## Marker Design

- **Shape**: Solid black circle (4-6mm diameter)
- **Direction indicator**: White line from center pointing towards the next marker
- **Recognition**: Circle detection + line angle extraction
- **Output**: `(found: bool, center: (x, y), angle: float, confidence: float)`

See `docs/markers/marker-design.md` for full specification.

---
For more detailed information, please refer to the documents in the `docs` directory.
