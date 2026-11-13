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

    /// Cancels an in-progress dwell when hand tracking is unavailable.
    mutating func trackingLost() {
        state = .idle
    }

    /// Prevents a semantic action committed elsewhere from repeating at the same position.
    mutating func beginCooldown(at committedPosition: SIMD3<Float>) {
        guard committedPosition.hasFiniteComponents else {
            trackingLost()
            return
        }
        state = .coolingDown(committedPosition: committedPosition)
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
