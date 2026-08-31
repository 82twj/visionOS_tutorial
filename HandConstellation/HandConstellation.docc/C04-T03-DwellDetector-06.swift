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
}
