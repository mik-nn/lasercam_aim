# product.md — Product Definition and User-Facing Capabilities

This document defines the product-level behaviour of the Marker Alignment Tool. It describes what the tool does, how users interact with it, and what guarantees it provides during the Print & Cut workflow.

## 1. Product Purpose

The tool assists users in aligning laser cuts to printed artwork by:

- detecting printed markers using a camera,
- moving the laser head to the marker centers,
- providing two-point alignment workflow,
- ensuring precise and repeatable alignment.

The tool reduces manual alignment errors and speeds up the workflow.

## 2. Target Users

The primary users are:

- hobbyists using LightBurn and consumer-grade laser cutters,
- professionals requiring precise alignment for production work,
- makers who frequently combine printing and laser cutting.

The tool must be simple enough for beginners and reliable enough for professionals.

## 3. Key Features

- Real-time camera preview  
- Automatic marker detection  
- Movement of laser to marker center  
- Integration with MeerK40t emulation plugins  
- Two-point alignment workflow  
- Simulator mode (MVP and optional in final tool)  
- Configurable camera and marker parameters  

These features must behave identically across MVP and final tool.

## 4. User Workflow Summary

1. Print artwork with markers.  
2. Place printed sheet on laser bed.  
3. Move camera to first marker.  
4. Tool detects marker and moves laser to center.  
5. User confirms point (M1 registered).
6. Repeat for second marker (M2).
7. Both alignment points are registered for cutting.

The tool guides the user through each step.

## 5. Product Guarantees

The tool guarantees:

- consistent marker detection behaviour,  
- accurate coordinate mapping,  
- correct sequencing of Print & Cut steps,  
- safe movement commands,  
- clear user feedback.

The tool must never move hardware without explicit user confirmation.

## 6. MVP vs Final Tool

The MVP provides:

- full simulation,  
- rapid experimentation,  
- algorithm validation.

The final tool provides:

- real hardware integration,  
- high performance,  
- production reliability.

Both share the same user-facing behaviour.

## 7. Non-Goals

The tool does not:

- modify LightBurn,  
- replace LightBurn’s Print & Cut logic,  
- perform full job execution,  
- control laser power or cutting parameters.

Its sole purpose is alignment assistance.

## 8. Future Extensions

Potential future features include:

- multi-marker alignment,  
- automatic sheet detection,  
- distortion compensation,  
- calibration wizards,  
- support for additional laser controllers.

These are out of scope for the initial release.