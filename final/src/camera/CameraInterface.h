// src/camera/CameraInterface.h
#ifndef CAMERAINTEFACE_H
#define CAMERAINTEFACE_H

#include <opencv2/core.hpp>
#include <tuple>

namespace lasercam {

// AICODE-NOTE: Abstract camera interface matching Python Camera module.
class CameraInterface {
public:
    virtual ~CameraInterface() = default;

    virtual cv::Mat get_frame() = 0;
    virtual std::tuple<int, int> resolution() const = 0;
    virtual void release() = 0;
};

} // namespace lasercam

#endif // CAMERAINTEFACE_H
