import simd

/// Stores the ordered points that form a constellation.
struct ConstellationModel: Sendable {
    struct Segment: Equatable, Sendable {
        let start: SIMD3<Float>
        let end: SIMD3<Float>
    }

    enum PointAddition: Equatable, Sendable {
        case added(position: SIMD3<Float>, segment: Segment?)
        case rejectedTooClose
        case rejectedLimitReached
        case rejectedInvalidPosition
    }
}
