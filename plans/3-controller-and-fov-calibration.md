# Plan 3 — Controller Integration and Camera FOV Calibration

## Objective

> "The camera is not tracking movement correctly. The camera's movement must be
> controlled via a controller (Ruida or GRBL). The camera's field of view must
> be adjusted to match the resolution."

Two root problems exist in the current MVP simulator:

1. **FOV / resolution mismatch** — `MotionSimulator.camera_fov_px` is computed
   as `fov_mm × workspace_pixels_per_mm`. This means the "camera image" is
   cropped at the workspace image's dot density (≈7.874 px/mm) rather than the
   camera's native sensor resolution. A real 1920×1080 camera over a 50×37 mm
   FOV has ≈38 px/mm — a completely different scale. The simulation must decouple
   workspace resolution from camera resolution.

2. **No controller abstraction** — movement is driven by direct calls into
   `MotionSimulator`. There is no path to real hardware (GRBL or Ruida). The UI
   bypasses any abstraction by importing `CameraSimulator` and reaching into its
   `.simulator` attribute directly.

---

## Proposed Steps

### Step 1 — Fix simulator FOV model

File: `mvp/simulator.py`

- Add `camera_resolution_px: tuple[int, int]` parameter (default `(1920, 1080)`).
- Keep `workspace_pixels_per_mm` (used only for the workspace background image).
- In `get_camera_view()`:
  1. Compute crop box in workspace pixels: `crop_w = fov_mm[0] × workspace_ppm`,
     `crop_h = fov_mm[1] × workspace_ppm`.
  2. Clip to work area bounds (already done).
  3. **`cv2.resize` the crop to `camera_resolution_px`** before returning.
- `camera_fov_px` now equals `camera_resolution_px` (the sensor resolution).
- The recognizer always receives a full-sensor-resolution image.
- Update `mvp/tests/test_simulator.py` accordingly.

### Step 2 — Add controller abstraction

New file: `mvp/controller.py`

```python
class BaseController(ABC):
    @property
    def position(self) -> tuple[float, float]: ...   # current (x_mm, y_mm)
    def move_to(self, x_mm: float, y_mm: float) -> None: ...
    def move_by(self, dx_mm: float, dy_mm: float) -> None: ...
    def move_in_direction(self, angle_deg: float, distance_mm: float) -> None: ...
    def release(self) -> None: ...

class SimulatedController(BaseController):
    """Thin wrapper around MotionSimulator — no behaviour change."""

class GRBLController(BaseController):
    """
    Sends G-code over a serial port.
    move_to  → G0 X{x:.3f} Y{y:.3f}\n  (absolute mode G90)
    move_by  → G91 + G0 + G90
    Reads position from ?-query (Grbl status report).
    Constructor: GRBLController(port, baudrate=115200)
    """

class RuidaController(BaseController):
    """
    Sends Ruida UDP move commands (port 50200).
    Protocol: move_to encodes an absolute XY packet.
    Constructor: RuidaController(host, port=50200)
    Stub implementation acceptable for MVP — real encoding added later.
    """
```

Add `mvp/tests/test_controller.py`:
- `test_simulated_controller_move_to`
- `test_simulated_controller_move_by`
- `test_simulated_controller_move_in_direction`
- GRBL and Ruida controllers are tested only for construction + interface
  conformance (no serial/network I/O needed in tests — use mocks).

### Step 3 — Wire controller through CameraSimulator and App

`mvp/camera_simulator.py`:
- Accept an optional `controller: BaseController` parameter. Default: create a
  `SimulatedController` internally.
- `move_to(x, y)` → `self.controller.move_to(x, y)`.
- `get_frame()` → reads position from `self.controller.position`, then asks
  the underlying `MotionSimulator` to render the view at that position.
- Expose `self.controller` as a public attribute.

`mvp/app.py`:
- Accept `controller_type: str` ("simulated" | "grbl" | "ruida") from env or
  config.
- Build the chosen controller and pass it to `CameraSimulator`.

### Step 4 — Refactor UI to use controller abstraction

`mvp/ui.py`:
- Remove all direct `isinstance(self.camera, CameraSimulator)` guards around
  movement. Movement always goes through `self.controller`.
- `App.__init__` receives an optional `controller: BaseController | None`. If
  `None`, infer from `self.camera` (backward-compatible).
- `move_gantry(dx, dy)` → `self.controller.move_by(dx, dy)` (no simulator
  import).
- `confirm_m1()` reads `self.controller.position` for `m1_camera_pos`.
- `_nav_step()` uses `self.controller.move_in_direction(...)`.
- Workspace boundary check uses `self.controller` geometry (only available for
  simulated; skip check for real hardware).
- Overview rendering stays gated on `isinstance(camera, CameraSimulator)` —
  only the simulator has a visual work area.
- Update `mvp/tests/test_ui.py` to inject a `SimulatedController` mock.

### Step 5 — Configuration module (minimal)

New file: `mvp/config.py` — simple dataclass / JSON loader:

```python
@dataclass
class Config:
    controller: str = "simulated"       # simulated | grbl | ruida
    grbl_port: str = "COM3"
    grbl_baudrate: int = 115200
    ruida_host: str = "192.168.1.100"
    ruida_port: int = 50200
    camera_resolution: tuple[int, int] = (1920, 1080)
    camera_fov_mm: tuple[float, float] = (50.0, 37.5)
    workspace_image: str = "Workspace90x60cm+sample.png"
    workspace_pixels_per_mm: float = 7087.0 / 900.0
    camera_start_x_mm: float = 780.0
    camera_start_y_mm: float = 493.0
```

Loaded from `lasercam.json` if present; defaults used otherwise.

### Step 6 — Update docs and tests

- Update `docs/simulator.md` with the corrected camera model.
- Update `docs/modules.md` to add the Controller module.
- Run full test suite and lint. Fix all failures.

---

## Risks / Open Questions

- **Ruida protocol**: The exact binary encoding of move commands is not yet
  defined. The stub raises `NotImplementedError` for real moves; this is
  acceptable for the MVP.
- **GRBL position polling**: The `?`-query response parsing must handle both
  Grbl 0.9 (`MPos`) and Grbl 1.1 (`WPos`/`MPos`) status formats.
- **Camera-to-machine coordinate offset**: The current code ignores the
  camera-to-laser offset during marker detection (laser is moved separately).
  This plan does not change that behaviour.
- **Workspace boundary check for real hardware**: With a real controller, the
  work area size is not known from an image. A configurable `(max_x_mm,
  max_y_mm)` field in `Config` is used instead.
- **Camera resolution choice**: The actual camera resolution for the GigE sensor
  must be confirmed by the user before the simulator can render at the correct
  scale. Default `(1920, 1080)` with a 50×37.5 mm FOV gives ≈38.4 px/mm.

---

## Rollback Strategy

All changes are additive (new `controller.py`, new `config.py`) or internal
refactors (no public API removed). The existing `MotionSimulator` and
`CameraSimulator` classes are extended, not replaced. Rolling back means
reverting the three modified files (`simulator.py`, `camera_simulator.py`,
`ui.py`) to the previous git commit.

---

## Awaiting Approval

Before implementation begins please confirm:

1. **Camera resolution**: what is the GigE camera's native resolution (px)?
2. **Camera FOV**: what physical area (mm × mm) does the camera see at the
   working distance used for alignment?
3. **Controller priority**: should GRBL or Ruida be the first real implementation
   (or both as stubs for now)?
4. **Config file**: is `lasercam.json` in the project root acceptable, or is
   another location / format preferred?
