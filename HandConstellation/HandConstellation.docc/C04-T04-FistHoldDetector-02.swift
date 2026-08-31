import Foundation

/// Converts a held fist pose into a single drawing-mode toggle.
struct FistHoldDetector: Sendable {
    enum Phase: Equatable, Sendable {
        case ready
        case holding
        case waitingForRelease
    }
}
