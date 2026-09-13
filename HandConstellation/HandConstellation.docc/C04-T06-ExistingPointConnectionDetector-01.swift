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
}
