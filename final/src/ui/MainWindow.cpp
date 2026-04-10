// src/ui/MainWindow.cpp
#include "ui/MainWindow.h"
#include "ui/CameraView.h"

namespace lasercam {

MainWindow::MainWindow(QWidget* parent)
    : QMainWindow(parent), camera_view_(nullptr) {
    // AICODE-TODO: Set up UI layout, menus, and connections
    camera_view_ = new CameraView(this);
    setCentralWidget(camera_view_);
}

MainWindow::~MainWindow() = default;

void MainWindow::on_update_frame() {
    // AICODE-TODO: Fetch frame from camera, detect markers, update view
}

void MainWindow::on_confirm_m1() {
    // AICODE-TODO: Confirm M1 marker, start navigation to M2
}

void MainWindow::on_confirm_m2() {
    // AICODE-TODO: Confirm M2 marker, complete alignment
}

void MainWindow::on_cancel() {
    // AICODE-TODO: Cancel current operation, return to idle
}

void MainWindow::on_move_gantry(double dx, double dy) {
    // AICODE-TODO: Move gantry via controller
    (void)dx; (void)dy;
}

} // namespace lasercam
