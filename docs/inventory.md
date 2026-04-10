# LaserCam Project Inventory

## Project Overview

**Project**: LaserCam — автоматизация LightBurn Print&Cut workflow для лазерных резаков

**Layers**:
- **MVP (Python)**: Rapid prototyping с эмуляторами камеры и контроллера
- **Final (C++/Qt)**: Production-ready standalone приложение

---

## MVP Python Modules

| Module | File | Description |
|--------|------|-------------|
| Entry | `main.py` | Точка входа, обёртка для app.py |
| App | `app.py` | Application initialization |
| Config | `config.py` | Конфигурация (JSON-based dataclass) |
| Controller | `controller.py` | BaseController, SimulatedController, GRBLController, RuidaController |
| Camera Simulator | `camera_simulator.py` | CameraSimulator с marker detection |
| Simulator | `simulator.py` | MotionSimulator — движения и FOV |
| Recognizer | `recognizer.py` | MarkerRecognizer — OpenCV detection |
| Bridge | `bridge.py` | LightBurnBridge (Real/Fake) — Alt+1/Alt+2 injection |
| UI | `ui.py` | Tkinter UI — состояния, Controls, Calibration |

---

## Final C++/Qt Modules

| Module | Path | Description |
|--------|------|-------------|
| Main | `final/src/main.cpp` | Entry point |
| UI | `final/src/ui/MainWindow.cpp`, `CameraView.cpp` | Qt main window + camera view |
| Controllers | `final/src/controllers/` | BaseController, RuidaController, GRBLController |
| Recognizer | `final/src/recognizer/MarkerRecognizer.cpp` | C++ marker detection |
| Calibration | `final/src/core/CalibrationManager.cpp` | Laser-camera offset calibration |

---

## External Dependencies

### Python (MVP)
- `opencv-python` — image processing
- `numpy` — numerical operations  
- `Pillow` — image I/O for Tkinter
- `pyserial` — GRBL serial communication
- `win32gui`, `win32con` — Windows API (hotkey injection)
- `pyautogui` — keyboard automation
- `pytest` — testing

### C++ (Final)
- `Qt` (Core, Gui, Widgets) — UI framework
- `OpenCV` — image processing
- `GoogleTest` / `Catch2` — testing

---

## State Machine

```
START → SEARCH_M1 → CONFIRM_M1 → REGISTER_M1 → SEARCH_M2 → CONFIRM_M2 → REGISTER_M2 → DONE → (auto) → START
```

---

## Workflow

1. Operator positions camera over M1 (via jog / LightBurn)
2. Selects "Register M1" in LightBurn Print&Cut
3. LaserCam detects marker, shows zoomed view + green circle
4. Operator fine-tunes position if needed
5. Operator confirms → LaserCam moves laser to marker centre
6. LaserCam sends Alt+1 to LightBurn (registers M1)
7. Operator selects "Register M2" in LightBurn Print&Cut
8. LaserCam determines direction from M1's marker line
9. LaserCam moves camera toward M2 autonomously
10. M2 enters FOV → LaserCam detects, shows zoomed view
11. Operator fine-tunes, confirms
12. LaserCam moves laser to M2 centre, sends Alt+2 to LightBurn
13. LightBurn now has both registration points → ready to cut

---

## Documentation Files

- `docs/architecture.md` — System architecture
- `docs/modules.md` — Module responsibilities
- `docs/markers/marker-design.md` — Marker format
- `docs/markers/direction-detection.md` — Direction detection
- `docs/markers/recognition-pipeline.md` — Detection workflow
- `docs/prototype/meerk40t-integration.md` — MeerK40T integration
- `docs/controllers/ruida-protocol.md` — RUIDA protocol
- `docs/controllers/grbl-protocol.md` — GRBL protocol
- `docs/calibration/laser-camera-offset.md` — Calibration system
- `docs/test-summary.md` — Test results

---

## Configuration

- `lasercam.json` — Runtime configuration (controller, ports, offsets, marker positions)
- `.flake8` — Python linting config
- `requirements.txt` / `requirements-dev.txt` — Python dependencies
- `final/CMakeLists.txt` — C++ build config
