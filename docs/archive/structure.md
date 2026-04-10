# structure.md — Project Structure and Architectural Layout

This document defines the overall structure of the Marker Alignment Tool project. It covers both the MVP (Python) and the final tool (C/C++/Qt), ensuring that the external behaviour remains consistent across both implementations.

## 1. High-Level Architecture

The project is divided into two layers:

- MVP layer: Python-based prototype used for rapid experimentation with marker detection, simulation, and workflow validation.
- Final layer: Native C/C++/Qt application used for production, hardware integration, and high-performance execution.

Both layers share the same conceptual modules and external behaviour.

## 2. Directory Layout

The repository is organized as follows:

docs/ — all documentation  
plans/ — agent-generated plans for complex tasks  
mvp/ — Python MVP implementation  
final/ — C/C++/Qt final implementation  
markers/ — marker templates and reference images  
simulator/ — simulation assets for MVP  
bridge/ — LightBurn integration logic  
config/ — configuration files  
tests/ — automated tests for MVP  

This structure ensures clear separation between prototype and production code.

## 3. Core Modules

The system consists of the following modules:

- Camera module  
- Marker recognizer  
- Motion simulator (MVP only)  
- Hardware driver (final tool only)  
- Coordinate mapping  
- LightBurn bridge  
- UI layer  
- Configuration module  
- Logging module  

Each module is documented in detail in modules.md.

## 4. Data Flow

The data flow is consistent across MVP and final tool:

Camera → Recognizer → Coordinate Mapping → Movement (simulated or real) → UI → LightBurn Bridge → State Machine

The state machine orchestrates the Print & Cut workflow.

## 5. MVP Structure

The MVP is implemented in Python and includes:

- DirectShow camera capture via OpenCV  
- Marker detection algorithms  
- Full simulation of gantry, camera, and laser  
- LightBurn bridge via Python WinAPI bindings  
- Simple UI for visualization and confirmation  

The MVP is used to validate algorithms and workflow before porting to native code.

## 6. Final Tool Structure

The final tool is implemented in C/C++/Qt and includes:

- Native DirectShow or Media Foundation camera capture  
- Optimized marker detection  
- Real hardware movement  
- Native WinAPI hooks for LightBurn integration  
- Qt-based UI  

The final tool must replicate the MVP’s external behaviour exactly.

## 7. External Behaviour Contract

The following behaviours must remain identical across MVP and final tool:

- Marker detection semantics  
- Movement to marker center  
- LightBurn hotkey handling  
- State machine transitions  
- User-facing workflow  

This ensures that the MVP is a reliable reference for the final implementation.

## 8. Evolution Path

1. Build and validate MVP.  
2. Finalize marker format and detection logic.  
3. Freeze external behaviour contract.  
4. Port stable components to C/C++/Qt.  
5. Replace simulator with real hardware integration.  
6. Maintain documentation and consistency across both layers.