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
}
