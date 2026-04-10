// src/ui/CameraView.h
#ifndef CAMERAVIEW_H
#define CAMERAVIEW_H

#include <QWidget>
#include <QImage>

namespace lasercam {

// AICODE-NOTE: Custom widget for displaying camera feed with
// marker overlays, crosshairs, and direction arrows.
class CameraView : public QWidget {
    Q_OBJECT

public:
    explicit CameraView(QWidget* parent = nullptr);

public slots:
    void set_frame(const QImage& image);
    void set_marker_overlay(double cx, double cy, double angle_deg,
                            double confidence);
    void clear_overlay();

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    QImage current_frame_;
    bool has_marker_;
    double marker_cx_;
    double marker_cy_;
    double marker_angle_;
    double marker_confidence_;
};

} // namespace lasercam

#endif // CAMERAVIEW_H
