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

    var points: [SIMD3<Float>] {
        constellations.flatMap { $0 }
    }

    var pointCount: Int {
        constellations.reduce(into: 0) { $0 += $1.count }
    }

    var constellationCount: Int {
        constellations.count
    }

    init(
        minimumPointDistance: Float = ConstellationConfiguration.standard.minimumPointDistance,
        maximumPointCount: Int = ConstellationConfiguration.standard.maximumPointCount
    ) {
        precondition(minimumPointDistance > 0)
        precondition(maximumPointCount > 0)
        self.minimumPointDistance = minimumPointDistance
        self.maximumPointCount = maximumPointCount
    }

    /// Adds a point when it is finite, sufficiently far away, and below the limit.
    mutating func addPoint(_ position: SIMD3<Float>) -> PointAddition {
        guard position.hasFiniteComponents else {
            return .rejectedInvalidPosition
        }

        guard pointCount < maximumPointCount else {
            return .rejectedLimitReached
        }

        let previousPoint = isStartingNewConstellation ? nil : constellations.last?.last
        if let previousPoint,
           simd_distance(previousPoint, position) < minimumPointDistance {
            return .rejectedTooClose
        }

        return .rejectedInvalidPosition
    }
}
