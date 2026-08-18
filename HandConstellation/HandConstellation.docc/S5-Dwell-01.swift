import Foundation
import simd

struct DwellDetector {
  enum Phase: Equatable { case idle, dwelling, coolingDown }

  struct Snapshot: Equatable {
    let phase: Phase
    let candidatePosition: SIMD3<Float>?
    let progress: Float
    let committedPosition: SIMD3<Float>?
  }
}
