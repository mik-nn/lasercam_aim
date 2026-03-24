# mvp/config.py
import json
from dataclasses import dataclass, asdict


@dataclass
class Config:
    controller: str = "simulated"
    grbl_port: str = "COM3"
    grbl_baudrate: int = 115200
    ruida_host: str = "192.168.1.100"
    ruida_port: int = 50200
    camera_resolution: tuple[int, int] = (1240, 720)
    camera_fov_mm: tuple[float, float] = (210.0, 122.0)
    workspace_image: str = "Workspace90x60cm+sample.png"
    workspace_pixels_per_mm: float = 7087.0 / 900.0  # approx 7.874
    camera_start_x_mm: float = 780.0
    camera_start_y_mm: float = 493.0
    # M1 = square marker (top-right of sample); M2 = circle marker (bottom-left).
    # Positions derived from camera start + card corner offsets in workspace coords.
    # Angles: direction each marker's internal dot points (toward the other marker).
    m1_x_mm: float = 809.2
    m1_y_mm: float = 480.3
    m1_angle_deg: float = 157.0
    m2_x_mm: float = 751.0
    m2_y_mm: float = 506.0
    m2_angle_deg: float = 337.0

    def save(self, path="lasercam.json"):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path="lasercam.json"):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return cls(**data)
        except FileNotFoundError:
            return cls()
