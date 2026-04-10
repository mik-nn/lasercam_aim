// src/main.cpp
#include <QApplication>
#include "ui/MainWindow.h"

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    app.setApplicationName("LaserCam");
    app.setApplicationVersion("0.1.0");

    lasercam::MainWindow window;
    window.resize(1024, 768);
    window.show();

    return app.exec();
}
