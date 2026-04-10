// src/core/CalibrationManager.h
#ifndef CALIBRATIONMANAGER_H
#define CALIBRATIONMANAGER_H

#include <cmath>
#include <string>
#include <tuple>

namespace lasercam {

using Offset = std::tuple<double, double>;

// AICODE-NOTE: Manages laser-camera offset calibration.
// Matches Python CalibrationManager interface.
class CalibrationManager {
public:
    CalibrationManager();

    void calibrate(double camera_x, double camera_y,
                   double laser_x, double laser_y);
    bool verify(double expected_x, double expected_y,
                double actual_x, double actual_y) const;
    Offset apply_offset(double camera_x, double camera_y) const;

    void set_threshold(double threshold_mm);
    double threshold() const { return threshold_mm_; }

    Offset offset() const { return offset_; }

private:
    Offset offset_;
    double threshold_mm_;
};

} // namespace lasercam

#endif // CALIBRATIONMANAGER_H
