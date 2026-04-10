// src/controllers/RuidaController.cpp
#include "controllers/RuidaController.h"

namespace lasercam {

// AICODE-TODO: Implement with Qt QUdpSocket.
// This is a skeleton - full implementation requires:
// 1. QUdpSocket initialization
// 2. RUIDA packet encoding (header + command + coords + checksum)
// 3. Position polling via UDP query
// 4. Response parsing

RuidaController::RuidaController(const std::string& host, int port)
    : host_(host), port_(port), last_position_({0.0, 0.0}),
      udp_socket_(nullptr) {}

RuidaController::~RuidaController() {
    release();
}

Position RuidaController::position() const {
    return last_position_;
}

void RuidaController::move_to(double x_mm, double y_mm) {
    // TODO: Send UDP move packet
    last_position_ = {x_mm, y_mm};
}

void RuidaController::move_by(double dx_mm, double dy_mm) {
    auto [x, y] = position();
    move_to(x + dx_mm, y + dy_mm);
}

void RuidaController::release() {
    // TODO: Close UDP socket
}

} // namespace lasercam
