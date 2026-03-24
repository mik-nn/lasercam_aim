# simulator.py
import math

import numpy as np


class MotionSimulator:
    def __init__(
        self,
        work_area_size=(1000, 1000),
        camera_fov=(100, 100),
        workspace_pixels_per_mm=5,
        camera_resolution_px=(1920, 1080),
    ):
        # Work area is BGR by default
        self.work_area = (
            np.ones((work_area_size[1], work_area_size[0], 3), dtype=np.uint8) * 255
        )
        self.gantry_x = 0  # in mm
        self.gantry_y = 0  # in mm
        self.laser_offset_x = 10  # in mm
        self.laser_offset_y = 10  # in mm
        self.camera_fov_mm = camera_fov  # in mm
        self.workspace_pixels_per_mm = workspace_pixels_per_mm

        # AICODE-NOTE: camera_fov_px is the camera sensor resolution, NOT the
        # workspace crop size. The crop size is derived on the fly inside
        # get_camera_view() as fov_mm × workspace_pixels_per_mm.
        self.camera_fov_px = camera_resolution_px  # (width, height) in pixels

        # The camera is mounted on the gantry, its position is the gantry position
        self.camera_x_mm = self.gantry_x
        self.camera_y_mm = self.gantry_y

    def set_work_area_image(self, image):
        """Sets the background image for the work area."""
        self.work_area = image
        # Optionally update size if image is different
        print(
            f"Work area image set. "
            f"Size: {self.work_area.shape[1]}x{self.work_area.shape[0]}"
        )

    def get_camera_view(self):
        """
        Returns the simulated camera frame.

        The FOV region is cropped from the workspace image at the workspace
        pixel density (pixels_per_mm), then resized to the camera sensor
        resolution (camera_fov_px).  This correctly decouples the workspace
        image DPI from the camera's actual pixel resolution.
        """
        import cv2

        cam_x_px = int(self.camera_x_mm * self.workspace_pixels_per_mm)
        cam_y_px = int(self.camera_y_mm * self.workspace_pixels_per_mm)

        # Crop size in workspace pixels for the physical FOV
        crop_w = int(self.camera_fov_mm[0] * self.workspace_pixels_per_mm)
        crop_h = int(self.camera_fov_mm[1] * self.workspace_pixels_per_mm)

        start_x = max(0, cam_x_px - crop_w // 2)
        end_x = min(self.work_area.shape[1], cam_x_px + crop_w // 2)
        start_y = max(0, cam_y_px - crop_h // 2)
        end_y = min(self.work_area.shape[0], cam_y_px + crop_h // 2)

        crop = self.work_area[start_y:end_y, start_x:end_x]
        if crop.size == 0:
            return crop

        # Resize to the camera sensor resolution so the recognizer always
        # receives a full-resolution image regardless of workspace DPI.
        out_w, out_h = self.camera_fov_px  # camera_fov_px == camera_resolution
        return cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

    def add_marker(self, x_mm, y_mm, shape_type, target_angle_deg, rotate_deg=0):
        """
        Adds a marker of the specified type at the given position.
        The marker's arrow will point in the specified direction.
        rotate_deg: overall rotation of the sample (relative to machine X axis).
        """
        import os
        import tempfile

        import cv2

        from generate_marker import generate_marker

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Generate marker with the arrow pointing to the target,
            # taking into account the sample rotation.
            generate_marker(
                shape_type,
                target_angle_deg - rotate_deg,
                tmp_path,
                scale=self.workspace_pixels_per_mm,
            )
            marker_img = cv2.imread(tmp_path)
            if marker_img is not None:
                # Rotate the entire marker image if the sample is rotated
                if rotate_deg != 0:
                    h, w = marker_img.shape[:2]
                    M = cv2.getRotationMatrix2D((w // 2, h // 2), rotate_deg, 1.0)
                    marker_img = cv2.warpAffine(
                        marker_img, M, (w, h), borderValue=(255, 255, 255)
                    )

                h, w = marker_img.shape[:2]
                center_x_px = int(x_mm * self.workspace_pixels_per_mm)
                center_y_px = int(y_mm * self.workspace_pixels_per_mm)

                start_x = center_x_px - w // 2
                start_y = center_y_px - h // 2

                # Ensure we are within bounds
                y1, y2 = max(0, start_y), min(self.work_area.shape[0], start_y + h)
                x1, x2 = max(0, start_x), min(self.work_area.shape[1], start_x + w)

                if y2 <= y1 or x2 <= x1:
                    return

                marker_roi = marker_img[
                    y1 - start_y : y2 - start_y, x1 - start_x : x2 - start_x
                ]

                # AICODE-NOTE: solid overwrite (no transparency). The new marker
                # canvas is pure-white background + black strokes.  Writing the
                # whole tile erases any pre-existing marker artefacts at this
                # position, which is required when the workspace image already
                # contains old-style markers.
                if self.work_area[y1:y2, x1:x2].shape[:2] == marker_roi.shape[:2]:
                    self.work_area[y1:y2, x1:x2] = marker_roi
            else:
                print(f"Error: Could not load generated marker from {tmp_path}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def place_sample(
        self, image_path, center_x_mm, center_y_mm, rotate_deg=0, scale=1.0
    ):
        """
        Places a sample image on the work area with rotation, scaling and
        transparency. Rotation corners are transparent so the workspace
        background shows through.
        """
        import cv2
        import numpy as np

        sample = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if sample is None:
            print(f"Error: Could not load sample image from {image_path}")
            return

        # Handle scaling
        if scale != 1.0:
            h, w = sample.shape[:2]
            new_size = (int(w * scale), int(h * scale))
            sample = cv2.resize(sample, new_size, interpolation=cv2.INTER_LINEAR)

        h, w = sample.shape[:2]

        # Build a mask (all-white = card present); will be shrunk to 0 at
        # rotation corners so the workspace mesh shows through there.
        card_mask = np.ones((h, w), dtype=np.uint8) * 255

        if rotate_deg != 0:
            M = cv2.getRotationMatrix2D((w // 2, h // 2), rotate_deg, 1.0)
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])
            nW = int((h * sin) + (w * cos))
            nH = int((h * cos) + (w * sin))
            M[0, 2] += (nW / 2) - w // 2
            M[1, 2] += (nH / 2) - h // 2
            # Rotate sample (white fill for empty corners — overridden by mask)
            sample = cv2.warpAffine(sample, M, (nW, nH), borderValue=(255, 255, 255))
            # Rotate mask with black fill so corners become fully transparent
            card_mask = cv2.warpAffine(card_mask, M, (nW, nH), borderValue=0)

        h, w = sample.shape[:2]
        start_x = int(center_x_mm * self.workspace_pixels_per_mm) - w // 2
        start_y = int(center_y_mm * self.workspace_pixels_per_mm) - h // 2

        y1, y2 = max(0, start_y), min(self.work_area.shape[0], start_y + h)
        x1, x2 = max(0, start_x), min(self.work_area.shape[1], start_x + w)

        if y2 <= y1 or x2 <= x1:
            print(f"Sample at ({center_x_mm}, {center_y_mm}) is out of bounds")
            return

        oy1 = y1 - start_y
        oy2 = oy1 + (y2 - y1)
        ox1 = x1 - start_x
        ox2 = ox1 + (x2 - x1)

        sample_roi = sample[oy1:oy2, ox1:ox2]
        mask_roi = card_mask[oy1:oy2, ox1:ox2]
        work_roi = self.work_area[y1:y2, x1:x2]

        if sample.shape[2] == 4:
            # Use alpha channel if present; intersect with card_mask
            alpha = (sample_roi[:, :, 3].astype(float) * mask_roi / 255.0) / 255.0
        else:
            alpha = mask_roi.astype(float) / 255.0

        alpha_3ch = alpha[:, :, np.newaxis]
        blended = (
            sample_roi[:, :, :3] * alpha_3ch + work_roi * (1.0 - alpha_3ch)
        ).astype(np.uint8)
        self.work_area[y1:y2, x1:x2] = blended

        print(
            f"Sample placed at ({center_x_mm}, {center_y_mm}) "
            f"with scale {scale} and rotation {rotate_deg}"
        )

    def move_in_direction(self, angle_deg, distance_mm):
        """Moves the gantry in the specified direction by the given distance."""
        dx = distance_mm * math.cos(math.radians(angle_deg))
        dy = distance_mm * math.sin(math.radians(angle_deg))
        self.move_gantry_to(self.gantry_x + dx, self.gantry_y + dy)

    def move_gantry_to(self, x_mm, y_mm):
        """Moves the gantry to the specified position in mm."""
        self.gantry_x = x_mm
        self.gantry_y = y_mm
        self.camera_x_mm = self.gantry_x
        self.camera_y_mm = self.gantry_y
        print(f"Gantry moved to: ({self.gantry_x}, {self.gantry_y})")

    def move_laser_to_marker_center(self, marker_center_camera_px):
        """
        Moves the gantry so the laser is at the marker's center.
        marker_center_camera_px is the marker's center in the camera's
        view in pixels.
        """
        # 1. Convert marker center from camera view pixels to mm
        #    relative to camera center.
        m_off_x_px = marker_center_camera_px[0] - self.camera_fov_px[0] / 2
        m_off_y_px = marker_center_camera_px[1] - self.camera_fov_px[1] / 2

        m_off_x_mm = m_off_x_px / self.workspace_pixels_per_mm
        m_off_y_mm = m_off_y_px / self.workspace_pixels_per_mm

        # 2. Calculate the marker's absolute position in mm
        marker_abs_x_mm = self.camera_x_mm + m_off_x_mm
        marker_abs_y_mm = self.camera_y_mm + m_off_y_mm

        # 3. Calculate the target gantry position to align laser with marker
        target_gantry_x = marker_abs_x_mm - self.laser_offset_x
        target_gantry_y = marker_abs_y_mm - self.laser_offset_y

        self.move_gantry_to(target_gantry_x, target_gantry_y)
        print(f"Laser is now at marker center: ({marker_abs_x_mm}, {marker_abs_y_mm})")
