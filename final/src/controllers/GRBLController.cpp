// src/controllers/GRBLController.cpp
#include "controllers/GRBLController.h"

namespace lasercam {

// AICODE-TODO: Implement with Qt QSerialPort.
// This is a skeleton - full implementation requires:
// 1. QSerialPort initialization
// 2. G-code command formatting (G0 X Y)
// 3. Position polling via '?' query
// 4. Response parsing for Grbl 0.9 and 1.1 formats

GRBLController::GRBLController(const std::string& port, int baudrate)
    : port_(port), baudrate_(baudrate), last_position_({0.0, 0.0}),
      serial_port_(nullptr) {}

GRBLController::~GRBLController() {
    release();
}

Position GRBLController::position() const {
    return last_position_;
}

void GRBLController::move_to(double x_mm, double y_mm) {
    // TODO: Send G0 X{x} Y{y} via serial
    last_position_ = {x_mm, y_mm};
}

void GRBLController::move_by(double dx_mm, double dy_mm) {
    auto [x, y] = position();
    move_to(x + dx_mm, y + dy_mm);
}

void GRBLController::release() {
    // TODO: Close serial port
}

} // namespace lasercam
