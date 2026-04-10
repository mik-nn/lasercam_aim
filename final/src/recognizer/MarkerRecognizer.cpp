// src/recognizer/MarkerRecognizer.cpp
#include "recognizer/MarkerRecognizer.h"
#include <opencv2/imgproc.hpp>
#include <cmath>

namespace lasercam {

MarkerRecognizer::MarkerRecognizer(
    double min_area_px,
    double max_area_px,
    double circularity_threshold,
    double line_length_min_ratio,
    double line_center_tolerance_ratio
)
    : min_area_px_(min_area_px),
      max_area_px_(max_area_px),
      circularity_threshold_(circularity_threshold),
      line_length_min_ratio_(line_length_min_ratio),
      line_center_tolerance_ratio_(line_center_tolerance_ratio) {}

MarkerResult MarkerRecognizer::find_marker(const cv::Mat& frame, std::optional<cv::Point2f> exclude_center_px, double exclude_radius_px) {
    if (frame.empty()) {
        return {false, std::nullopt, std::nullopt, 0.0};
    }

    // AICODE-NOTE: Port of Python find_marker() algorithm.
    // Same steps: grayscale -> blur -> invert -> threshold -> contours.
    cv::Mat gray, blurred, inverted, thresh;
    cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
    cv::GaussianBlur(gray, blurred, cv::Size(5, 5), 0);
    inverted = 255 - blurred;
    cv::threshold(inverted, thresh, 128, 255, cv::THRESH_BINARY);

    std::vector<std::vector<cv::Point>> contours;
    cv::findContours(thresh, contours, cv::RETR_EXTERNAL,
                     cv::CHAIN_APPROX_SIMPLE);

    struct Candidate {
        cv::Point2f center;
        double angle;
        double confidence;
    };

    std::vector<Candidate> candidates;

    for (const auto& contour : contours) {
        double area = cv::contourArea(contour);
        if (area < min_area_px_ || area > max_area_px_) continue;

        double peri = cv::arcLength(contour, true);
        if (peri == 0) continue;

        double circularity = 4 * M_PI * area / (peri * peri);
        if (circularity < circularity_threshold_) continue;

        cv::Moments m = cv::moments(contour);
        if (m.m00 == 0) continue;

        float cx = static_cast<float>(m.m10 / m.m00);
        float cy = static_cast<float>(m.m01 / m.m00);

        if (exclude_center_px.has_value()) {
            double dist = std::sqrt(std::pow(cx - exclude_center_px->x, 2) + std::pow(cy - exclude_center_px->y, 2));
            if (dist < exclude_radius_px) continue;
        }

        float radius = std::sqrt(static_cast<float>(area / M_PI));

        auto [angle, line_conf] = detect_line(frame, cx, cy, radius);
        if (angle.has_value()) {
            double confidence = circularity * line_conf;
            candidates.push_back({{cx, cy}, *angle, confidence});
        }
    }

    if (candidates.empty()) {
        return {false, std::nullopt, std::nullopt, 0.0};
    }

    // Return best candidate
    auto best = *std::max_element(candidates.begin(), candidates.end(),
        [](const Candidate& a, const Candidate& b) {
            return a.confidence < b.confidence;
        });

    return {true, best.center, best.angle, best.confidence};
}

std::tuple<std::optional<double>, double> MarkerRecognizer::detect_line(
    const cv::Mat& frame, float cx, float cy, float radius
) {
    if (frame.empty()) return {std::nullopt, 0.0};

    int margin = static_cast<int>(radius * 0.3f);
    int x1 = std::max(0, static_cast<int>(cx - radius - margin));
    int y1 = std::max(0, static_cast<int>(cy - radius - margin));
    int x2 = std::min(frame.cols, static_cast<int>(cx + radius + margin));
    int y2 = std::min(frame.rows, static_cast<int>(cy + radius + margin));

    if (x2 <= x1 || y2 <= y1) return {std::nullopt, 0.0};

    cv::Mat roi = frame(cv::Range(y1, y2), cv::Range(x1, x2));
    if (roi.empty()) return {std::nullopt, 0.0};

    cv::Mat roi_gray, white_mask;
    cv::cvtColor(roi, roi_gray, cv::COLOR_BGR2GRAY);
    cv::threshold(roi_gray, white_mask, 200, 255, cv::THRESH_BINARY);

    // Mask to circle region
    cv::Mat circle_mask = cv::Mat::zeros(white_mask.size(), CV_8UC1);
    int cx_roi = static_cast<int>(cx - x1);
    int cy_roi = static_cast<int>(cy - y1);
    cv::circle(circle_mask, {cx_roi, cy_roi}, static_cast<int>(radius),
               255, -1);
    cv::bitwise_and(white_mask, white_mask, white_mask, circle_mask);

    std::vector<std::vector<cv::Point>> white_contours;
    cv::findContours(white_mask, white_contours, cv::RETR_EXTERNAL,
                     cv::CHAIN_APPROX_SIMPLE);

    if (white_contours.empty()) return {std::nullopt, 0.0};

    double best_angle = 0.0;
    double best_confidence = 0.0;
    bool found = false;

    for (const auto& wc : white_contours) {
        double wc_area = cv::contourArea(wc);
        if (wc_area < 3) continue;

        cv::Moments m = cv::moments(wc);
        if (m.m00 == 0) continue;

        double wc_cx = m.m10 / m.m00;
        double wc_cy = m.m01 / m.m00;
        double dx = wc_cx - cx_roi;
        double dy = wc_cy - cy_roi;
        double dist = std::sqrt(dx * dx + dy * dy);

        double min_dist = radius * line_length_min_ratio_;
        double max_dist = radius * 1.1;

        if (dist >= min_dist && dist <= max_dist) {
            double angle = std::atan2(dy, dx) * 180.0 / M_PI;
            if (angle < 0) angle += 360.0;

            double optimal_dist = radius * 0.65;
            double dist_score = 1.0 - std::abs(dist - optimal_dist) / optimal_dist;
            dist_score = std::max(0.0, std::min(1.0, dist_score));

            double expected_line_area = radius * radius * 0.06;
            double area_score = std::min(1.0, wc_area / expected_line_area);

            double confidence = dist_score * area_score;
            confidence = std::max(0.0, std::min(1.0, confidence));

            if (confidence > best_confidence) {
                best_confidence = confidence;
                best_angle = angle;
                found = true;
            }
        }
    }

    if (found && best_confidence > 0.05) {
        return {best_angle, best_confidence};
    }
    return {std::nullopt, 0.0};
}

} // namespace lasercam
