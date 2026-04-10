cmake_minimum_required(VERSION 3.16)
project(LaserCam VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Find dependencies
find_package(Qt6 COMPONENTS Core Gui Widgets Network QUIET)
if(NOT Qt6_FOUND)
    find_package(Qt5 5.15 REQUIRED COMPONENTS Core Gui Widgets Network)
    set(QT_VERSION_MAJOR 5)
else()
    set(QT_VERSION_MAJOR 6)
endif()

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)

# Source files
set(SOURCES
    src/main.cpp
    src/core/BaseController.cpp
    src/core/CalibrationManager.cpp
    src/recognizer/MarkerRecognizer.cpp
    src/controllers/GRBLController.cpp
    src/controllers/RuidaController.cpp
    src/ui/MainWindow.cpp
    src/ui/CameraView.cpp
)

set(HEADERS
    src/core/BaseController.h
    src/core/CalibrationManager.h
    src/core/AppState.h
    src/camera/CameraInterface.h
    src/recognizer/MarkerRecognizer.h
    src/controllers/GRBLController.h
    src/controllers/RuidaController.h
    src/ui/MainWindow.h
    src/ui/CameraView.h
)

# Main executable
add_executable(lasercam ${SOURCES} ${HEADERS})

target_link_libraries(lasercam PRIVATE
    Qt${QT_VERSION_MAJOR}::Core
    Qt${QT_VERSION_MAJOR}::Gui
    Qt${QT_VERSION_MAJOR}::Widgets
    Qt${QT_VERSION_MAJOR}::Network
    ${OpenCV_LIBS}
)

target_include_directories(lasercam PRIVATE
    src
)

# Tests (optional, requires Google Test)
option(BUILD_TESTS "Build tests" OFF)
if(BUILD_TESTS)
    include(FetchContent)
    FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
    )
    FetchContent_MakeAvailable(googletest)

    enable_testing()

    add_executable(lasercam_tests
        tests/test_recognizer.cpp
        tests/test_calibration.cpp
        tests/test_controllers.cpp
    )

    target_link_libraries(lasercam_tests PRIVATE
        GTest::gtest_main
        Qt${QT_VERSION_MAJOR}::Core
        ${OpenCV_LIBS}
    )

    target_include_directories(lasercam_tests PRIVATE src)

    add_test(NAME LaserCamTests COMMAND lasercam_tests)
endif()

# Install
install(TARGETS lasercam DESTINATION bin)
