import simd

/// Stores the ordered points that form one constellation.
struct Constellation: Equatable, Sendable {
    private(set) var points: [SIMD3<Float>]
    private(set) var isClosed = false

    init(points: [SIMD3<Float>]) {
        self.points = points
    }

    mutating func append(_ point: SIMD3<Float>) {
        points.append(point)
    }

    mutating func close() {
        isClosed = true
    }
}

/// Stores the ordered constellations and decides which points and segments are valid.
struct ConstellationModel: Sendable {
    struct Segment: Equatable, Sendable {
        let start: SIMD3<Float>
        let end: SIMD3<Float>
    }

    enum PointAddition: Equatable, Sendable {
        case added(position: SIMD3<Float>, segment: Segment?)
        case closed(segment: Segment)
        case rejectedTooClose
        case rejectedLimitReached
        case rejectedInvalidPosition
        case rejectedNotClosable
    }

    let minimumPointDistance: Float
    let maximumPointCount: Int
    private(set) var constellations: [Constellation] = []
    private var isStartingNewConstellation = true

    var points: [SIMD3<Float>] {
        constellations.flatMap(\.points)
    }

    var pointCount: Int {
        constellations.reduce(into: 0) { $0 += $1.points.count }
    }

    var constellationCount: Int {
        constellations.count
    }

    var currentConstellationPoints: [SIMD3<Float>] {
        guard !isStartingNewConstellation else { return [] }
        return constellations.last?.points ?? []
    }

    var canCloseCurrentConstellation: Bool {
        currentConstellationPoints.count >= 3
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

    /// Adds a distinct point when it is finite and below the global limit.
    mutating func addPoint(_ position: SIMD3<Float>) -> PointAddition {
        guard position.hasFiniteComponents else {
            return .rejectedInvalidPosition
        }

        guard pointCount < maximumPointCount else {
            return .rejectedLimitReached
        }

        if currentConstellationPoints.contains(where: {
            simd_distance($0, position) < minimumPointDistance
        }) {
            return .rejectedTooClose
        }

        let previousPoint = currentConstellationPoints.last
        let segment = previousPoint.map { Segment(start: $0, end: position) }

        if isStartingNewConstellation {
            constellations.append(Constellation(points: [position]))
            isStartingNewConstellation = false
        } else {
            constellations[constellations.count - 1].append(position)
        }

        return .added(position: position, segment: segment)
    }

    /// Reuses the exact first point and adds only the final segment.
    mutating func closeCurrentConstellation() -> PointAddition {
        guard canCloseCurrentConstellation,
              let firstPoint = currentConstellationPoints.first,
              let lastPoint = currentConstellationPoints.last,
              simd_distance(firstPoint, lastPoint) > .ulpOfOne else {
            return .rejectedNotClosable
        }

        let segment = Segment(start: lastPoint, end: firstPoint)
        constellations[constellations.count - 1].close()
        isStartingNewConstellation = true
        return .closed(segment: segment)
    }

    /// Finishes an open constellation so that the next point starts a new one.
    mutating func finishCurrentConstellation() {
        isStartingNewConstellation = true
    }

    /// Removes every constellation and point.
    mutating func reset() {
        constellations.removeAll(keepingCapacity: true)
        isStartingNewConstellation = true
    }
}
