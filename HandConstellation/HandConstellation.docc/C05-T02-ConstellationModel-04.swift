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

    let minimumPointDistance: Float
    let maximumPointCount: Int
    private(set) var constellations: [[SIMD3<Float>]] = []
    private var isStartingNewConstellation = true
}
