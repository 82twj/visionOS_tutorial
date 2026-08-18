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

  private enum State: Equatable {
    case idle
    case dwelling(center: SIMD3<Float>, startedAt: TimeInterval)
    case coolingDown(committedPosition: SIMD3<Float>)
  }

  let dwellDuration: TimeInterval
  let stabilityRadius: Float
  let rearmDistance: Float
  private var state: State = .idle

  init(dwellDuration: TimeInterval = 0.8, stabilityRadius: Float = 0.015, rearmDistance: Float = 0.030) {
    self.dwellDuration = dwellDuration
    self.stabilityRadius = stabilityRadius
    self.rearmDistance = rearmDistance
  }
}
