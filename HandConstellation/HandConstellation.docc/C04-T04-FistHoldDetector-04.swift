import Foundation

/// Converts a held fist pose into a single drawing-mode toggle.
struct FistHoldDetector: Sendable {
    enum Phase: Equatable, Sendable {
        case ready
        case holding
        case waitingForRelease
    }

    struct Snapshot: Equatable, Sendable {
        let phase: Phase
        let progress: Float
        let didToggle: Bool
    }

    private enum State: Equatable, Sendable {
        case ready
        case holding(startedAt: TimeInterval)
        case waitingForRelease
    }
}
