import cv2
import numpy as np
import argparse
import math


def create_base_image(marker_size_mm, scale):
    size_px = int(marker_size_mm * scale)
    image = np.ones((size_px, size_px, 3), dtype=np.uint8) * 255
    return image, size_px // 2


def generate_marker(shape_type, target_angle_deg, output_path, scale=20):
    """
    Generates a marker image.

    Design 1 — Clean Outline + Offset Internal Dot:
      - Outer boundary: square or circle stroke (NO external arrow head).
        This guarantees a clean, uninterrupted outer contour so that
        approxPolyDP always yields exactly 4 points for a square and high
        circularity for a circle.
      - Direction indicator: a single filled dot placed INSIDE the shape at
        1 mm from centre in the direction of target_angle_deg.  Its centroid
        offset from the shape centre is what the recogniser uses to derive the
        angle (atan2 of grandchild centroid vs parent centroid).

    shape_type: 'square' or 'circle'
    target_angle_deg: angle towards the other marker (image coords, 0=east, 90=south)
    """
    marker_size_mm = 16.0
    shape_size_mm = 4.0
    stroke_width_mm = 0.5

    image, center_px = create_base_image(marker_size_mm, scale)
    center = (center_px, center_px)

    color = (0, 0, 0)
    stroke_px = max(1, int(stroke_width_mm * scale))
    shape_px = int(shape_size_mm * scale)

    if shape_type == "square":
        half = shape_px // 2
        cv2.rectangle(
            image,
            (center_px - half, center_px - half),
            (center_px + half, center_px + half),
            color,
            stroke_px,
        )
    elif shape_type == "circle":
        cv2.circle(image, center, shape_px // 2, color, stroke_px)

    # Direction indicator: offset solid dot INSIDE the shape.
    # Placed at dot_offset_mm from centre in the direction of the target.
    # Radius chosen so the dot is clearly detectable at camera resolution
    # (~6 px at 7.874 px/mm workspace) while staying inside the stroke boundary.
    dot_offset_mm = 1.0
    dot_radius_mm = 0.6
    angle_rad = math.radians(target_angle_deg)
    dx = int(round(dot_offset_mm * scale * math.cos(angle_rad)))
    dy = int(round(dot_offset_mm * scale * math.sin(angle_rad)))
    dot_center = (center_px + dx, center_px + dy)
    dot_radius = max(2, int(dot_radius_mm * scale))
    cv2.circle(image, dot_center, dot_radius, color, -1)

    cv2.imwrite(output_path, image)
    print(
        f"Generated {shape_type} marker at {output_path} "
        f"with angle {target_angle_deg} deg"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate markers for LaserCam")
    parser.add_argument(
        "--type", choices=["square", "circle"], required=True, help="Marker shape type"
    )
    parser.add_argument(
        "--angle", type=float, default=0, help="Angle in degrees for the direction dot"
    )
    parser.add_argument(
        "--output", type=str, default="marker.png", help="Output file path"
    )
    parser.add_argument(
        "--scale", type=int, default=20, help="Pixels per mm (DPI equivalent)"
    )
    args = parser.parse_args()
    generate_marker(args.type, args.angle, args.output, args.scale)
