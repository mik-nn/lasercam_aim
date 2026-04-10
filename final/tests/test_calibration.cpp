// tests/test_calibration.cpp
#include <gtest/gtest.h>
#include "core/CalibrationManager.h"

TEST(CalibrationManagerTest, InitialOffsetIsZero) {
    lasercam::CalibrationManager mgr;
    auto [dx, dy] = mgr.offset();
    EXPECT_DOUBLE_EQ(dx, 0.0);
    EXPECT_DOUBLE_EQ(dy, 0.0);
}

TEST(CalibrationManagerTest, CalibrateSetsOffset) {
    lasercam::CalibrationManager mgr;
    mgr.calibrate(0, 0, 10, 5);
    auto [dx, dy] = mgr.offset();
    EXPECT_DOUBLE_EQ(dx, 10.0);
    EXPECT_DOUBLE_EQ(dy, 5.0);
}

TEST(CalibrationManagerTest, ApplyOffset) {
    lasercam::CalibrationManager mgr;
    mgr.calibrate(0, 0, 10, 10);
    auto [lx, ly] = mgr.apply_offset(50, 30);
    EXPECT_DOUBLE_EQ(lx, 60.0);
    EXPECT_DOUBLE_EQ(ly, 40.0);
}

TEST(CalibrationManagerTest, VerifyWithinThreshold) {
    lasercam::CalibrationManager mgr;
    mgr.set_threshold(0.1);
    EXPECT_TRUE(mgr.verify(10.0, 10.0, 10.05, 10.05));
}

TEST(CalibrationManagerTest, VerifyExceedsThreshold) {
    lasercam::CalibrationManager mgr;
    mgr.set_threshold(0.1);
    EXPECT_FALSE(mgr.verify(10.0, 10.0, 10.5, 10.5));
}
