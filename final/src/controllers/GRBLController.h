// src/controllers/GRBLController.h
#ifndef GRBLCONTROLLER_H
#define GRBLCONTROLLER_H

#include "core/BaseController.h"
#include <string>

namespace lasercam {

// AICODE-NOTE: GRBL serial controller matching Python GRBLController.
// Uses Qt's QSerialPort for cross-platform serial communication.
class GRBLController : public BaseController {
public:
    GRBLController(const std::string& port, int baudrate = 115200);
    ~GRBLController() override;

    Position position() const override;
    void move_to(double x_mm, double y_mm) override;
    void move_by(double dx_mm, double dy_mm) override;
    void release() override;

private:
    std::string port_;
    int baudrate_;
    mutable Position last_position_;
    void* serial_port_; // QSerialPort* - forward declared to avoid Qt include
};

} // namespace lasercam

#endif // GRBLCONTROLLER_H
