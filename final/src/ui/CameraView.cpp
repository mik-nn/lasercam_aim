// src/ui/CameraView.cpp
#include "ui/CameraView.h"
#include <QPainter>

namespace lasercam {

CameraView::CameraView(QWidget* parent)
    : QWidget(parent), has_marker_(false), marker_cx_(0), marker_cy_(0),
      marker_angle_(0), marker_confidence_(0) {}

void CameraView::set_frame(const QImage& image) {
    current_frame_ = image;
    update();
}

void CameraView::set_marker_overlay(double cx, double cy, double angle_deg,
                                    double confidence) {
    has_marker_ = true;
    marker_cx_ = cx;
    marker_cy_ = cy;
    marker_angle_ = angle_deg;
    marker_confidence_ = confidence;
    update();
}

void CameraView::clear_overlay() {
    has_marker_ = false;
    update();
}

void CameraView::paintEvent(QPaintEvent* event) {
    Q_UNUSED(event);
    QPainter painter(this);

    if (!current_frame_.isNull()) {
        painter.drawImage(rect(), current_frame_);
    }

    if (has_marker_) {
        // Draw circle
        painter.setPen(QPen(Qt::green, 2));
        painter.drawEllipse(QPoint(static_cast<int>(marker_cx_),
                                   static_cast<int>(marker_cy_)),
                            20, 20);

        // Draw direction arrow
        painter.setPen(QPen(Qt::yellow, 2));
        double rad = marker_angle_ * 3.14159 / 180.0;
        int ex = static_cast<int>(marker_cx_ + 40 * std::cos(rad));
        int ey = static_cast<int>(marker_cy_ + 40 * std::sin(rad));
        painter.drawLine(QPoint(static_cast<int>(marker_cx_),
                                static_cast<int>(marker_cy_)),
                         QPoint(ex, ey));
    }
}

} // namespace lasercam
