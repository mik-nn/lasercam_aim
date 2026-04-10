# vision.md — Marker Design and Detection Principles

This document defines the visual marker system used by the Marker Alignment Tool. It covers marker design, detection assumptions, geometric constraints, and the requirements that must remain stable across both the MVP (Python) and the final tool (C/C++/Qt).

## 1. Purpose of the Marker System

The markers provide fixed reference points printed on the material. The camera detects these markers, computes their centers, and the tool moves the laser head to these positions. LightBurn uses these two points to compute the affine transform for Print & Cut alignment.

The marker system must be:
- easy to detect,
- robust to lighting variations,
- tolerant to print imperfections,
- stable across different cameras and resolutions,
- simple enough for real-time processing.

## 2. Marker Structure

The marker consists of:
- a high-contrast outer shape,
- a unique internal pattern for validation,
- a well-defined geometric center.

The MVP may experiment with several designs, but the final tool must standardize on one stable format.

## 3. Detection Assumptions

The recognizer assumes:
- the marker is fully visible in the camera frame,
- the marker is not rotated beyond the recognizer’s tolerance,
- the marker has sufficient contrast relative to the background,
- the camera resolution is adequate for subpixel center estimation.

The MVP may use simple thresholding and contour analysis. The final tool may use more advanced methods, but the external behaviour must remain identical.

## 4. Required Outputs

The recognizer must output:
- found: boolean
- center: (x, y) in image coordinates
- orientation: optional angle
- confidence: numeric score

These outputs must be consistent across MVP and final tool.

## 5. Geometric Constraints

The marker must:
- have a clearly defined center,
- be symmetric enough for stable detection,
- be large enough to survive print noise,
- be small enough to fit on typical printed artwork.

The exact dimensions are defined in the marker template file (not included here).

## 6. Robustness Requirements

The marker must remain detectable under:
- uneven lighting,
- slight blur,
- minor print distortions,
- camera noise,
- perspective distortion within reasonable limits.

The MVP is used to validate these constraints experimentally.

## 7. Finalization Process

The marker design becomes final when:
- the MVP recognizer achieves stable detection across test prints,
- the simulator confirms correct alignment behaviour,
- the final tool can reproduce the same detection results.

Once finalized, the marker format becomes part of the public contract of the tool.