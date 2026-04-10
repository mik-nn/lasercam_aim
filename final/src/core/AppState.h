// src/core/AppState.h
#ifndef APPSTATE_H
#define APPSTATE_H

#include <string>

namespace lasercam {

// AICODE-NOTE: Application state machine matching Python UI states.
enum class AppState {
    Idle,
    Detected,
    Approved,
    Moving,
    Calibrating,
    Cancelled,
};

inline std::string state_to_string(AppState state) {
    switch (state) {
        case AppState::Idle:       return "IDLE";
        case AppState::Detected:   return "DETECTED";
        case AppState::Approved:   return "APPROVED";
        case AppState::Moving:     return "MOVING";
        case AppState::Calibrating: return "CALIBRATING";
        case AppState::Cancelled:  return "CANCELLED";
        default:                   return "UNKNOWN";
    }
}

} // namespace lasercam

#endif // APPSTATE_H
