// tests/test_recognizer.cpp
#include <gtest/gtest.h>
#include "recognizer/MarkerRecognizer.h"

// AICODE-TODO: These tests require OpenCV to be available.
// They mirror the Python tests in mvp/tests/test_recognizer.py.

TEST(MarkerRecognizerTest, EmptyFrameReturnsNotFound) {
    lasercam::MarkerRecognizer recognizer;
    cv::Mat empty_frame;
    auto [found, center, angle, confidence] = recognizer.find_marker(empty_frame);
    EXPECT_FALSE(found);
    EXPECT_FALSE(center.has_value());
    EXPECT_FALSE(angle.has_value());
    EXPECT_DOUBLE_EQ(confidence, 0.0);
}
