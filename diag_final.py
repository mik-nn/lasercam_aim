import sys
sys.path.insert(0, '.')
from mvp.camera_simulator import CameraSimulator
from mvp.config import Config

cfg = Config.load()
cam = CameraSimulator(
    workspace_image_path=cfg.workspace_image,
    camera_fov=cfg.camera_fov_mm,
    workspace_pixels_per_mm=cfg.workspace_pixels_per_mm,
    camera_resolution_px=cfg.camera_resolution,
)
cam.add_marker(cfg.m1_x_mm, cfg.m1_y_mm, 'square', cfg.m1_angle_deg)
cam.add_marker(cfg.m2_x_mm, cfg.m2_y_mm, 'circle', cfg.m2_angle_deg)
cam.move_to(cfg.camera_start_x_mm, cfg.camera_start_y_mm)

found, center, shape, angle = cam.find_marker()
print(f'M1 (square preferred): found={found}, shape={shape}, center={center}, angle={angle:.1f}')
assert found and shape == 'square', 'FAIL: expected square'

# Simulate moving close to M2 (move camera center to M2)
cam.move_to(cfg.m2_x_mm, cfg.m2_y_mm)
found, center, shape, angle = cam.find_marker()
print(f'M2 (at circle pos): found={found}, shape={shape}, center={center}, angle={angle:.1f}')
assert found, 'FAIL: expected marker at M2 position'

print('ALL OK')
