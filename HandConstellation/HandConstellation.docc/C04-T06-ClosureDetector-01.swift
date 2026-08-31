import Foundation
import simd

/// Recognizes an intentional dwell near the first point of an open constellation.
struct ClosureDetector: Sendable {
    enum Phase: Equatable, Sendable {
        case idle
        case available
        case dwelling
    }

    struct Snapshot: Equatable, Sendable {
        let phase: Phase
        let targetPosition: SIMD3<Float>?
        let progress: Float
        let didCommit: Bool
    }

    let dwellDuration: TimeInterval
    let snapDistance: Float
    let releaseDistance: Float
    let departureDistance: Float

    private var hasDepartedLastPoint = false
    private var startedAt: TimeInterval?
    private var isInsideTarget = false

    init(
        dwellDuration: TimeInterval = ConstellationConfiguration.standard.dwellDuration,
        snapDistance: Float = ConstellationConfiguration.standard.closureSnapDistance,
        releaseDistance: Float = ConstellationConfiguration.standard.closureReleaseDistance,
        departureDistance: Float = ConstellationConfiguration.standard.stabilityRadius
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

    /// Processes the fingertip against the first point after at least three points exist.
    mutating func update(
        position: SIMD3<Float>,
        firstPoint: SIMD3<Float>?,
        lastPoint: SIMD3<Float>?,
        pointCount: Int,
        at timestamp: TimeInterval
    ) -> Snapshot {
        guard pointCount >= 3,
              let firstPoint,
              let lastPoint,
              position.hasFiniteComponents,
              firstPoint.hasFiniteComponents,
              lastPoint.hasFiniteComponents,
              timestamp.isFinite else {
            reset()
            return idleSnapshot
        }

        if !hasDepartedLastPoint {
            hasDepartedLastPoint = simd_distance(position, lastPoint) >= departureDistance
            guard hasDepartedLastPoint else {
                return availableSnapshot(target: firstPoint)
            }
        }

        let distanceToTarget = simd_distance(position, firstPoint)

        if isInsideTarget {
            guard distanceToTarget <= releaseDistance, let startedAt else {
                cancelCandidate()
                return availableSnapshot(target: firstPoint)
            }

            let elapsed = max(0, timestamp - startedAt)
            let progress = Float(min(1, elapsed / dwellDuration))
            let didCommit = elapsed + 1e-9 >= dwellDuration

            if didCommit {
                cancelCandidate()
                hasDepartedLastPoint = false
            }

            return Snapshot(
                phase: .dwelling,
                targetPosition: firstPoint,
                progress: progress,
                didCommit: didCommit
            )
        }

        guard distanceToTarget <= snapDistance else {
            return availableSnapshot(target: firstPoint)
        }

        isInsideTarget = true
        startedAt = timestamp
        return Snapshot(
            phase: .dwelling,
            targetPosition: firstPoint,
            progress: 0,
            didCommit: false
        )
    }

    /// Requires the fingertip to leave the latest point again before closing.
    mutating func pointCommitted() {
        hasDepartedLastPoint = false
        cancelCandidate()
    }

    /// Cancels progress when tracking becomes unavailable.
    mutating func trackingLost() {
        hasDepartedLastPoint = false
        cancelCandidate()
    }

    mutating func reset() {
        hasDepartedLastPoint = false
        cancelCandidate()
    }

    private mutating func cancelCandidate() {
        isInsideTarget = false
        startedAt = nil
    }

    private func availableSnapshot(target: SIMD3<Float>) -> Snapshot {
        Snapshot(
            phase: .available,
            targetPosition: target,
            progress: 0,
            didCommit: false
        )
    }

    private var idleSnapshot: Snapshot {
        Snapshot(phase: .idle, targetPosition: nil, progress: 0, didCommit: false)
    }
}
