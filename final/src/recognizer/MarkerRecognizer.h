// src/recognizer/MarkerRecognizer.h
#ifndef MARKERRECOGNIZER_H
#define MARKERRECOGNIZER_H

#include <opencv2/core.hpp>
#include <tuple>
#include <optional>

namespace lasercam {

// AICODE-NOTE: Port of Python MarkerRecognizer to C++.
// Same detection semantics: circle + direction line.
using MarkerResult = std::tuple<
    bool,                       // found
    std::optional<cv::Point2f>, // center
    std::optional<double>,      // angle_deg
    double                      // confidence
>;

class MarkerRecognizer {
public:
    MarkerRecognizer(
        double min_area_px = 50.0,
        double max_area_px = 50000.0,
        double circularity_threshold = 0.7,
        double line_length_min_ratio = 0.28,
        double line_center_tolerance_ratio = 0.4
    );

    MarkerResult find_marker(const cv::Mat& frame, std::optional<cv::Point2f> exclude_center_px = std::nullopt, double exclude_radius_px = 15.0);

private:
    std::tuple<std::optional<double>, double> detect_line(
        const cv::Mat& frame, float cx, float cy, float radius
    );

    double min_area_px_;
    double max_area_px_;
    double circularity_threshold_;
    double line_length_min_ratio_;
    double line_center_tolerance_ratio_;
};

} // namespace lasercam

#endif // MARKERRECOGNIZER_H
