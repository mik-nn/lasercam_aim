// tests/test_controllers.cpp
#include <gtest/gtest.h>
#include "controllers/GRBLController.h"
#include "controllers/RuidaController.h"

// AICODE-TODO: These tests require Qt and serial/UDP hardware mocking.
// They mirror the Python tests in mvp/tests/test_controller.py.

TEST(GRBLControllerTest, Construction) {
    // AICODE-TODO: Mock QSerialPort for testing
    // GRBLController ctrl("COM3", 115200);
    // EXPECT_EQ(ctrl.position(), (std::tuple{0.0, 0.0}));
}

TEST(RuidaControllerTest, Construction) {
    // AICODE-TODO: Mock QUdpSocket for testing
    // RuidaController ctrl("192.168.1.100", 50200);
    // EXPECT_EQ(ctrl.position(), (std::tuple{0.0, 0.0}));
}
