import cv2
import numpy as np
import argparse
import math


def create_base_image(marker_size_mm, scale):
    size_px = int(marker_size_mm * scale)
    image = np.ones((size_px, size_px, 3), dtype=np.uint8) * 255
    return image, size_px // 2


def generate_marker(shape_type, target_angle_deg, output_path, scale: float = 20):
    """
    Generates a marker image.

    Design: Solid Fill + White Direction Line
      - Outer shape: solid black filled square (M1) or circle (M2), 4 mm.
        A solid fill gives a clean, unambiguous outer contour — no stroke
        irregularities at camera resolution.
      - Direction indicator: a white filled line (thick rectangle) drawn
        FROM the shape centre TOWARD the other marker.  It creates a single
        child contour whose centroid is offset from the shape centre.
        Child area / outer area ≈ 0.08 → falls in the recogniser's direct-
        child branch (0.005 < ratio < 0.2), giving reliable detection.
      - No external elements: the 16 mm canvas around the 4 mm shape is
        pure white, so it composites cleanly over any workspace background.

    shape_type        : 'square' or 'circle'
    target_angle_deg  : angle toward the other marker (image coords,
                        0 = east / right, 90 = south / down)
    """
    marker_size_mm = 16.0   # canvas (white border around the 4 mm shape)
    shape_size_mm = 4.0     # outer filled shape diameter / side length
    line_length_mm = 1.6    # white line from centre to this distance
    line_width_mm = 0.8     # width of the white line indicator

    image, center_px = create_base_image(marker_size_mm, scale)
    center = (center_px, center_px)

    shape_px = int(shape_size_mm * scale)

    # --- Solid filled outer shape ---
    if shape_type == "square":
        half = shape_px // 2
        cv2.rectangle(
            image,
            (center_px - half, center_px - half),
            (center_px + half, center_px + half),
            (0, 0, 0),
            -1,  # filled
        )
    elif shape_type == "circle":
        cv2.circle(image, center, shape_px // 2, (0, 0, 0), -1)

    # --- White direction line from centre toward target ---
    # The line is drawn as a thick white stroke starting at the shape centre
    # and extending line_length_mm in the direction of target_angle_deg.
    # After THRESH_BINARY_INV, this white region becomes a "hole" (child
    # contour) inside the solid black shape.  Its centroid displacement
    # encodes the direction angle.
    # AICODE-NOTE: thickness must be ≥ 2px at every supported scale to
    # survive Gaussian blur in the recogniser.
    angle_rad = math.radians(target_angle_deg)
    end_x = center_px + int(round(line_length_mm * scale * math.cos(angle_rad)))
    end_y = center_px + int(round(line_length_mm * scale * math.sin(angle_rad)))
    line_thickness_px = max(2, int(line_width_mm * scale))
    cv2.line(image, center, (end_x, end_y), (255, 255, 255), line_thickness_px)

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
        "--angle", type=float, default=0, help="Angle in degrees for the direction line"
    )
    parser.add_argument(
        "--output", type=str, default="marker.png", help="Output file path"
    )
    parser.add_argument(
        "--scale", type=int, default=20, help="Pixels per mm (DPI equivalent)"
    )
    args = parser.parse_args()
    generate_marker(args.type, args.angle, args.output, args.scale)
