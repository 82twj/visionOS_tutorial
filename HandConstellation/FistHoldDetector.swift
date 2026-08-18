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

    let holdDuration: TimeInterval
    private var state: State = .ready

    init(holdDuration: TimeInterval = ConstellationConfiguration.standard.fistHoldDuration) {
        precondition(holdDuration > 0)
        self.holdDuration = holdDuration
    }

    /// Processes whether the tracked hand currently forms a fist.
    mutating func update(isFist: Bool, at timestamp: TimeInterval) -> Snapshot {
        guard timestamp.isFinite else {
            reset()
            return readySnapshot
        }

        guard isFist else {
            state = .ready
            return readySnapshot
        }

        switch state {
        case .ready:
            state = .holding(startedAt: timestamp)
            return Snapshot(phase: .holding, progress: 0, didToggle: false)

        case .holding(let startedAt):
            let elapsed = max(0, timestamp - startedAt)
            let progress = Float(min(1, elapsed / holdDuration))

            guard elapsed + 1e-9 >= holdDuration else {
                return Snapshot(phase: .holding, progress: progress, didToggle: false)
            }

            state = .waitingForRelease
            return Snapshot(phase: .waitingForRelease, progress: 1, didToggle: true)

        case .waitingForRelease:
            return Snapshot(phase: .waitingForRelease, progress: 1, didToggle: false)
        }
    }

    mutating func reset() {
        state = .ready
    }

    private var readySnapshot: Snapshot {
        Snapshot(phase: .ready, progress: 0, didToggle: false)
    }
}
