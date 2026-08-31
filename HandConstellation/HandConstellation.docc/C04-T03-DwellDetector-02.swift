import Foundation
import simd

/// Converts a stream of spatial positions into deliberate dwell commitments.
struct DwellDetector: Sendable {
    enum Phase: Equatable, Sendable {
        case idle
        case dwelling
        case coolingDown
    }
}
