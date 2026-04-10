// src/controllers/RuidaController.h
#ifndef RUIDACONTROLLER_H
#define RUIDACONTROLLER_H

#include "core/BaseController.h"
#include <string>

namespace lasercam {

// AICODE-NOTE: RUIDA UDP controller matching Python RuidaController.
// Uses Qt's QUdpSocket for UDP communication.
class RuidaController : public BaseController {
public:
    RuidaController(const std::string& host, int port = 50200);
    ~RuidaController() override;

    Position position() const override;
    void move_to(double x_mm, double y_mm) override;
    void move_by(double dx_mm, double dy_mm) override;
    void release() override;

private:
    std::string host_;
    int port_;
    mutable Position last_position_;
    void* udp_socket_; // QUdpSocket* - forward declared
};

} // namespace lasercam

#endif // RUIDACONTROLLER_H
