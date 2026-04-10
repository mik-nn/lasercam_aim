// src/core/BaseController.h
#ifndef BASECONTROLLER_H
#define BASECONTROLLER_H

#include <cmath>
#include <tuple>

namespace lasercam {

using Position = std::tuple<double, double>;

// AICODE-NOTE: Abstract base class matching Python BaseController interface.
// All concrete controllers inherit from this.
class BaseController {
public:
    virtual ~BaseController() = default;

    virtual Position position() const = 0;
    virtual void move_to(double x_mm, double y_mm) = 0;
    virtual void move_by(double dx_mm, double dy_mm) = 0;

    void move_in_direction(double angle_deg, double distance_mm) {
        double rad = angle_deg * M_PI / 180.0;
        double dx = distance_mm * std::cos(rad);
        double dy = distance_mm * std::sin(rad);
        move_by(dx, dy);
    }

    virtual void release() = 0;
};

} // namespace lasercam

#endif // BASECONTROLLER_H
