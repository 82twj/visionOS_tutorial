import simd

struct ConstellationModel {
  struct Segment: Equatable {
    let start: SIMD3<Float>
    let end: SIMD3<Float>
  }

  enum PointAddition: Equatable {
    case added(position: SIMD3<Float>, segment: Segment?)
    case rejectedTooClose
    case rejectedLimitReached
    case rejectedInvalidPosition
  }
  let minimumPointDistance: Float
  let maximumPointCount: Int
  private(set) var constellations: [[SIMD3<Float>]] = []
  private var isStartingNewConstellation = true
  var pointCount: Int {
    constellations.reduce(into: 0) { $0 += $1.count }
  }

  var constellationCount: Int {
    constellations.count
  }

  init(minimumPointDistance: Float = 0.030, maximumPointCount: Int = 100) {
    self.minimumPointDistance = minimumPointDistance
    self.maximumPointCount = maximumPointCount
  }

  mutating func addPoint(_ position: SIMD3<Float>) -> PointAddition {
    guard position.hasFiniteComponents else { return .rejectedInvalidPosition }
    guard pointCount < maximumPointCount else { return .rejectedLimitReached }

    let previousPoint = isStartingNewConstellation ? nil : constellations.last?.last
    if let previousPoint,
      simd_distance(previousPoint, position) < minimumPointDistance
    {
      return .rejectedTooClose
    }

    return .rejectedInvalidPosition
  }
}
