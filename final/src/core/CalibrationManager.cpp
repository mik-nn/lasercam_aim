// src/core/CalibrationManager.cpp
#include "core/CalibrationManager.h"

namespace lasercam {

CalibrationManager::CalibrationManager()
    : offset_(0.0, 0.0), threshold_mm_(0.1) {}

void CalibrationManager::calibrate(double camera_x, double camera_y,
                                   double laser_x, double laser_y) {
    offset_ = {laser_x - camera_x, laser_y - camera_y};
}

bool CalibrationManager::verify(double expected_x, double expected_y,
                                double actual_x, double actual_y) const {
    double dx = expected_x - actual_x;
    double dy = expected_y - actual_y;
    double deviation = std::sqrt(dx * dx + dy * dy);
    return deviation <= threshold_mm_;
}

Offset CalibrationManager::apply_offset(double camera_x, double camera_y) const {
    return {camera_x + std::get<0>(offset_),
            camera_y + std::get<1>(offset_)};
}

void CalibrationManager::set_threshold(double threshold_mm) {
    threshold_mm_ = threshold_mm;
}

} // namespace lasercam
