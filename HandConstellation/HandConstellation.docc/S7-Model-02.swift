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

  private(set) var constellations: [[SIMD3<Float>]] = []
  private var isStartingNewConstellation = true

  var pointCount: Int {
    constellations.reduce(into: 0) { $0 += $1.count }
  }

  var constellationCount: Int {
    constellations.count
  }
}
