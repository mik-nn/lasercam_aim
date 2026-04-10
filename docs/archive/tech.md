# tech.md — Technology Stack and Implementation Details

This document defines the technologies used in both the MVP and the final tool. It ensures that the implementation remains consistent, maintainable, and aligned with the project’s goals.

## 1. MVP Technology Stack (Python)

The MVP uses:

- Python 3
- OpenCV for image processing
- DirectShow backend for camera capture
- Tkinter for UI
- pyserial for GRBL serial communication
- socket for RUIDA UDP communication
- MeerK40t plugins for emulation (HTTP API)
- JSON-based configuration files

The MVP prioritizes rapid iteration and experimentation.

## 2. Final Tool Technology Stack (C/C++/Qt)

The final tool uses:

- C++17 for core logic
- Qt (5/6) for UI and application framework
- OpenCV for marker detection
- DirectShow or Media Foundation for camera capture
- QSerialPort for GRBL communication
- QUdpSocket for RUIDA communication
- MeerK40t emulation plugins (HTTP API)
- Structured configuration files

The final tool prioritizes performance and reliability.

## 3. Shared Technologies

Both MVP and final tool use:

- OpenCV for image processing  
- DirectShow-compatible camera  
- Identical marker detection semantics  
- Identical coordinate mapping logic  
- Identical state machine for Print & Cut  

This ensures consistent behaviour across implementations.

## 4. Build and Packaging

MVP:

- Python environment  
- Standard Python packaging  
- Optional virtual environment  

Final tool:

- CMake-based build system  
- Qt deployment tools  
- Static or dynamic linking depending on platform  

Packaging must produce a standalone executable for end users.

## 5. Performance Considerations

The final tool must:

- process camera frames in real time,  
- maintain stable FPS,  
- minimize latency between detection and movement,  
- avoid blocking UI threads,  
- ensure safe hardware control.

The MVP may use simplified or slower approaches.

## 6. Platform Requirements

The tool targets:

- Windows 10 and later  
- DirectShow-compatible cameras  
- LightBurn running on Windows  

Linux and macOS are out of scope for the initial release.

## 7. External Dependencies

The project depends on:

- OpenCV  
- Qt (final tool)  
- WinAPI  
- DirectShow or Media Foundation  

Dependencies must be documented and versioned.