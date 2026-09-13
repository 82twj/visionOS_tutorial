import Foundation
import simd

/// Recognizes an intentional dwell near any existing point in the active constellation.
struct ExistingPointConnectionDetector: Sendable {
    struct Target: Equatable, Sendable {
        let nodeID: Int
        let position: SIMD3<Float>
        let isAlreadyConnected: Bool
    }

    enum Phase: Equatable, Sendable {
        case idle
        case available
        case dwelling
    }

    struct Snapshot: Equatable, Sendable {
        let phase: Phase
        let target: Target?
        let progress: Float
        let didCommit: Bool
    }

    let dwellDuration: TimeInterval
    let snapDistance: Float
    let releaseDistance: Float
    let departureDistance: Float

    private var hasDepartedActivePoint = false
    private var lockedTarget: Target?
    private var startedAt: TimeInterval?

    init(
        dwellDuration: TimeInterval = ConstellationConfiguration.standard.dwellDuration,
        snapDistance: Float = ConstellationConfiguration.standard.connectionSnapDistance,
        releaseDistance: Float = ConstellationConfiguration.standard.connectionReleaseDistance,
        departureDistance: Float = ConstellationConfiguration.standard.rearmDistance
    ) {
        precondition(dwellDuration > 0)
        precondition(snapDistance > 0)
        precondition(releaseDistance >= snapDistance)
        precondition(departureDistance > 0)
        self.dwellDuration = dwellDuration
        self.snapDistance = snapDistance
        self.releaseDistance = releaseDistance
        self.departureDistance = departureDistance
    }

    mutating func update(
        position: SIMD3<Float>,
        activePoint: SIMD3<Float>?,
        targets: [Target],
        at timestamp: TimeInterval
    ) -> Snapshot {
        guard let activePoint,
              !targets.isEmpty,
              position.hasFiniteComponents,
              activePoint.hasFiniteComponents,
              targets.allSatisfy({ $0.position.hasFiniteComponents }),
              timestamp.isFinite else {
            reset()
            return idleSnapshot
        }

        if !hasDepartedActivePoint {
            hasDepartedActivePoint = simd_distance(position, activePoint) >= departureDistance
            guard hasDepartedActivePoint else {
                return availableSnapshot
            }
        }
        return availableSnapshot
    }

    mutating func pointCommitted() {
        hasDepartedActivePoint = false
        cancelCandidate()
    }

    mutating func trackingLost() {
        hasDepartedActivePoint = false
        cancelCandidate()
    }

    mutating func reset() {
        hasDepartedActivePoint = false
        cancelCandidate()
    }

    private mutating func cancelCandidate() {
        lockedTarget = nil
        startedAt = nil
    }

    private var availableSnapshot: Snapshot {
        Snapshot(phase: .available, target: nil, progress: 0, didCommit: false)
    }

    private var idleSnapshot: Snapshot {
        Snapshot(phase: .idle, target: nil, progress: 0, didCommit: false)
    }
}
