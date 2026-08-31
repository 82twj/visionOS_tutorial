import Foundation
import simd

/// Converts a stream of spatial positions into deliberate dwell commitments.
struct DwellDetector: Sendable {
    enum Phase: Equatable, Sendable {
        case idle
        case dwelling
        case coolingDown
    }

    struct Snapshot: Equatable, Sendable {
        let phase: Phase
        let candidatePosition: SIMD3<Float>?
        let progress: Float
        let committedPosition: SIMD3<Float>?
    }

    private enum State: Equatable, Sendable {
        case idle
        case dwelling(center: SIMD3<Float>, startedAt: TimeInterval)
        case coolingDown(committedPosition: SIMD3<Float>)
    }

    let dwellDuration: TimeInterval
    let stabilityRadius: Float
    let rearmDistance: Float
    private var state: State = .idle

    init(
        dwellDuration: TimeInterval = ConstellationConfiguration.standard.dwellDuration,
        stabilityRadius: Float = ConstellationConfiguration.standard.stabilityRadius,
        rearmDistance: Float = ConstellationConfiguration.standard.rearmDistance
    ) {
        precondition(dwellDuration > 0)
        precondition(stabilityRadius > 0)
        precondition(rearmDistance > 0)
        self.dwellDuration = dwellDuration
        self.stabilityRadius = stabilityRadius
        self.rearmDistance = rearmDistance
    }

    /// Processes a valid fingertip position at a monotonic timestamp.
    mutating func update(position: SIMD3<Float>, at timestamp: TimeInterval) -> Snapshot {
        guard position.hasFiniteComponents, timestamp.isFinite else {
            trackingLost()
            return idleSnapshot
        }

        switch state {
        case .idle:
            state = .dwelling(center: position, startedAt: timestamp)
            return Snapshot(
                phase: .dwelling,
                candidatePosition: position,
                progress: 0,
                committedPosition: nil
            )

        case .dwelling(let center, let startedAt):
            guard simd_distance(center, position) <= stabilityRadius else {
                state = .dwelling(center: position, startedAt: timestamp)
                return Snapshot(
                    phase: .dwelling,
                    candidatePosition: position,
                    progress: 0,
                    committedPosition: nil
                )
            }

            let elapsed = max(0, timestamp - startedAt)
            let progress = Float(min(1, elapsed / dwellDuration))
            let hasReachedDwellDuration = elapsed + 1e-9 >= dwellDuration

            guard hasReachedDwellDuration else {
                return Snapshot(
                    phase: .dwelling,
                    candidatePosition: center,
                    progress: progress,
                    committedPosition: nil
                )
            }

            state = .coolingDown(committedPosition: center)
            return Snapshot(
                phase: .coolingDown,
                candidatePosition: center,
                progress: 1,
                committedPosition: center
            )

        case .coolingDown(let committedPosition):
            guard simd_distance(committedPosition, position) >= rearmDistance else {
                return Snapshot(
                    phase: .coolingDown,
                    candidatePosition: committedPosition,
                    progress: 0,
                    committedPosition: nil
                )
            }

            state = .dwelling(center: position, startedAt: timestamp)
            return Snapshot(
                phase: .dwelling,
                candidatePosition: position,
                progress: 0,
                committedPosition: nil
            )
        }
    }

    /// Cancels an in-progress dwell when hand tracking is unavailable.
    mutating func trackingLost() {
        state = .idle
    }

    /// Returns the detector to its initial state.
    mutating func reset() {
        state = .idle
    }

    private var idleSnapshot: Snapshot {
        Snapshot(phase: .idle, candidatePosition: nil, progress: 0, committedPosition: nil)
    }
}

extension SIMD3 where Scalar == Float {
    var hasFiniteComponents: Bool {
        x.isFinite && y.isFinite && z.isFinite
    }
}
