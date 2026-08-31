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
}
