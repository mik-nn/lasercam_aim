# C++ Application Architecture

## 1. Overview

This document defines the architecture for the final LaserCam C++ application. The application replicates the MVP's external behaviour exactly while providing high performance, robustness, and production reliability.

---

## 2. Technology Stack

| Component | Technology |
|-----------|------------|
| Language | C++17 |
| UI Framework | Qt 6 |
| Image Processing | OpenCV 4.x |
| Build System | CMake 3.20+ |
| Testing | Google Test |
| Serial Communication | Qt Serial Port |
| Network Communication | Qt Network |
| Configuration | JSON (nlohmann/json) |

---

## 3. Project Structure

```
lasercam/
├── CMakeLists.txt
├── src/
│   ├── main.cpp
│   ├── app/
│   │   ├── application.h
│   │   ├── application.cpp
│   │   └── state_machine.h
│   ├── recognizer/
│   │   ├── marker_recognizer.h
│   │   ├── marker_recognizer.cpp
│   │   ├── circle_detector.h
│   │   ├── circle_detector.cpp
│   │   ├── line_detector.h
│   │   └── line_detector.cpp
│   ├── controller/
│   │   ├── base_controller.h
│   │   ├── simulated_controller.h
│   │   ├── simulated_controller.cpp
│   │   ├── grbl_controller.h
│   │   ├── grbl_controller.cpp
│   │   ├── ruida_controller.h
│   │   └── ruida_controller.cpp
│   ├── calibration/
│   │   ├── calibration_manager.h
│   │   ├── calibration_manager.cpp
│   │   └── offset_tracker.h
│   ├── camera/
│   │   ├── camera_interface.h
│   │   ├── directshow_camera.h
│   │   ├── directshow_camera.cpp
│   │   ├── emulator_camera.h
│   │   └── emulator_camera.cpp
│   ├── ui/
│   │   ├── main_window.h
│   │   ├── main_window.cpp
│   │   ├── camera_view.h
│   │   ├── camera_view.cpp
│   │   ├── control_panel.h
│   │   └── control_panel.cpp
│   └── common/
│       ├── types.h
│       ├── config.h
│       ├── config.cpp
│       ├── logger.h
│       └── logger.cpp
├── tests/
│   ├── test_recognizer.cpp
│   ├── test_controller.cpp
│   ├── test_calibration.cpp
│   └── test_integration.cpp
├── resources/
│   ├── icons/
│   └── translations/
└── docs/
```

---

## 4. Core Components

### 4.1 Application Core

The `Application` class orchestrates all components:

```cpp
class Application : public QObject {
    Q_OBJECT
public:
    Application();
    void initialize();
    void run();
    void shutdown();

signals:
    void stateChanged(AppState newState);
    void markerDetected(const MarkerDetection& detection);
    void errorOccurred(const QString& message);

private:
    std::unique_ptr<CameraInterface> camera_;
    std::unique_ptr<BaseController> controller_;
    std::unique_ptr<MarkerRecognizer> recognizer_;
    std::unique_ptr<CalibrationManager> calibration_;
    std::unique_ptr<MainWindow> mainWindow_;
    AppState state_;
};
```

### 4.2 State Machine

```cpp
enum class AppState {
    Idle,
    Detected,
    Approved,
    Moving,
    Calibrating,
    Cancelled,
    Error
};

class StateMachine : public QObject {
    Q_OBJECT
public:
    void transitionTo(AppState newState);
    AppState currentState() const;
    bool canTransitionTo(AppState newState) const;

signals:
    void stateChanged(AppState newState);
};
```

**State Transitions:**
```
Idle → Detected (marker found)
Detected → Approved (user confirms)
Detected → Idle (user cancels)
Approved → Moving (start movement)
Moving → Calibrating (movement complete)
Calibrating → Idle (calibration passed)
Calibrating → Error (calibration failed)
Any → Cancelled (user cancels)
Any → Error (error occurred)
Error → Idle (error cleared)
```

---

## 5. Module Interfaces

### 5.1 Marker Recognizer

```cpp
struct MarkerDetection {
    bool found;
    QPointF center;        // In image coordinates (pixels)
    double angleDeg;       // Direction angle (0° = east, 90° = south)
    double confidence;     // 0.0 - 1.0
};

class MarkerRecognizer {
public:
    MarkerDetection detect(const cv::Mat& frame);
    void configure(const RecognizerConfig& config);

private:
    std::unique_ptr<CircleDetector> circleDetector_;
    std::unique_ptr<LineDetector> lineDetector_;
};
```

### 5.2 Controller Abstraction

```cpp
class BaseController {
public:
    virtual ~BaseController() = default;
    
    virtual QPointF position() const = 0;
    virtual void moveTo(double xMm, double yMm) = 0;
    virtual void moveBy(double dxMm, double dyMm) = 0;
    virtual void moveInDirection(double angleDeg, double distanceMm);
    virtual void stop() = 0;
    virtual bool isConnected() const = 0;
    
signals:
    void positionChanged(QPointF newPosition);
    void errorOccurred(const QString& message);
};
```

**Concrete Implementations:**
- `SimulatedController`: For testing without hardware
- `GRBLController`: Serial communication with GRBL
- `RuidaController`: UDP communication with Ruida

### 5.3 Camera Interface

```cpp
class CameraInterface {
public:
    virtual ~CameraInterface() = default;
    
    virtual bool initialize() = 0;
    virtual cv::Mat getFrame() = 0;
    virtual void release() = 0;
    virtual CameraInfo info() const = 0;
    
signals:
    void frameReady(const cv::Mat& frame);
    void errorOccurred(const QString& message);
};
```

**Concrete Implementations:**
- `DirectShowCamera`: Real camera capture on Windows
- `EmulatorCamera`: Receives frames from MeerK40t camera emulator

### 5.4 Calibration Manager

```cpp
struct CalibrationData {
    QPointF offsetMm;          // Laser-camera offset
    double thresholdMm;        // Maximum allowed deviation
    QDateTime lastCalibrated;
    QPointF calibrationPosition;
};

class CalibrationManager : public QObject {
    Q_OBJECT
public:
    CalibrationData calibrate(QPointF cameraPos, QPointF laserPos);
    bool verify(QPointF expectedPos, QPointF actualPos);
    QPointF applyOffset(QPointF cameraPosition) const;
    void loadFromFile(const QString& path);
    void saveToFile(const QString& path);

signals:
    void offsetChanged(QPointF newOffset);
    void calibrationRequired();
};
```

---

## 6. Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Camera    │────▶│  Recognizer  │────▶│     UI       │
│  (frames)   │     │ (detection)  │     │ (display)    │
└─────────────┘     └──────┬───────┘     └──────┬───────┘
                           │                    │
                    ┌──────▼───────┐     ┌──────▼───────┐
                    │     User     │     │  Controller  │
                    │  (approve)   │     │  (movement)  │
                    └──────────────┘     └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │ Calibration  │
                                         │   (verify)   │
                                         └──────────────┘
```

---

## 7. Configuration

### 7.1 Configuration File (lasercam.json)

```json
{
    "application": {
        "controller_type": "simulated",
        "camera_type": "emulator",
        "language": "en"
    },
    "controller": {
        "grbl": {
            "port": "COM3",
            "baudrate": 115200
        },
        "ruida": {
            "host": "192.168.1.100",
            "port": 50200
        }
    },
    "camera": {
        "device_index": 0,
        "resolution": [1920, 1080],
        "fov_mm": [50.0, 37.5]
    },
    "emulator": {
        "laser_host": "127.0.0.1",
        "laser_port": 8080,
        "camera_host": "127.0.0.1",
        "camera_port": 8081
    },
    "recognizer": {
        "min_area_px": 50,
        "max_area_px": 50000,
        "circularity_threshold": 0.8
    },
    "calibration": {
        "offset_x_mm": 10.0,
        "offset_y_mm": 10.0,
        "threshold_mm": 0.1,
        "verification_interval": 10
    }
}
```

---

## 8. Build System

### 8.1 CMakeLists.txt (Root)

```cmake
cmake_minimum_required(VERSION 3.20)
project(LaserCam VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets SerialPort Network)
find_package(OpenCV REQUIRED)
find_package(nlohmann_json REQUIRED)

add_subdirectory(src)
add_subdirectory(tests)
```

### 8.2 Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Qt 6 | 6.5+ | UI, Serial, Network |
| OpenCV | 4.8+ | Image processing |
| nlohmann/json | 3.11+ | Configuration |
| Google Test | 1.14+ | Testing |

---

## 9. Threading Model

- **UI Thread**: Qt event loop, user interaction
- **Camera Thread**: Frame capture and delivery
- **Recognizer Thread**: Image processing (offloaded from UI)
- **Controller Thread**: Movement commands and position polling
- **Calibration Thread**: Offset verification (periodic)

All inter-thread communication uses Qt signals/slots with `Qt::QueuedConnection`.

---

## 10. Error Handling

### 10.1 Error Types

```cpp
enum class ErrorCode {
    CameraInitFailed,
    ControllerConnectionFailed,
    RecognizerError,
    MovementFailed,
    CalibrationFailed,
    Timeout,
    InvalidConfiguration
};

struct LaserCamError {
    ErrorCode code;
    QString message;
    QString details;
};
```

### 10.2 Error Recovery

| Error | Recovery Action |
|-------|-----------------|
| Camera init failed | Retry 3 times, then show error dialog |
| Controller disconnected | Attempt reconnection, notify user |
| Recognition error | Skip frame, continue processing |
| Movement failed | Stop immediately, report error |
| Calibration failed | Recalibrate, or use last known offset |

---

## 11. Testing Strategy

### 11.1 Unit Tests

- Marker recognition algorithms
- Controller command generation
- Calibration calculations
- Configuration loading/saving

### 11.2 Integration Tests

- Camera → Recognizer pipeline
- Recognizer → Controller workflow
- Full application state machine

### 11.3 System Tests

- End-to-end workflow with emulator
- Performance benchmarks
- Memory leak detection
