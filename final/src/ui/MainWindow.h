// src/ui/MainWindow.h
#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace lasercam {

class CameraView;

// AICODE-NOTE: Main application window matching Python Tkinter UI.
// Shows camera preview, marker overlays, controls, and workspace overview.
class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(QWidget* parent = nullptr);
    ~MainWindow() override;

private slots:
    void on_update_frame();
    void on_confirm_m1();
    void on_confirm_m2();
    void on_cancel();
    void on_move_gantry(double dx, double dy);

private:
    CameraView* camera_view_;
    // AICODE-TODO: Add controller, calibration manager, recognizer members
};

} // namespace lasercam

#endif // MAINWINDOW_H
