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

  init(
    dwellDuration: TimeInterval = 0.8, stabilityRadius: Float = 0.015, rearmDistance: Float = 0.030
  ) {
    self.dwellDuration = dwellDuration
    self.stabilityRadius = stabilityRadius
    self.rearmDistance = rearmDistance
  }

  mutating func update(position: SIMD3<Float>, at timestamp: TimeInterval) -> Snapshot {
    guard position.hasFiniteComponents, timestamp.isFinite else {
      state = .idle
      return idleSnapshot
    }

    switch state {
    case .idle:
      state = .dwelling(center: position, startedAt: timestamp)
      return Snapshot(
        phase: .dwelling, candidatePosition: position, progress: 0, committedPosition: nil)

    case .dwelling(let center, _):
      guard simd_distance(center, position) <= stabilityRadius else {
        state = .dwelling(center: position, startedAt: timestamp)
        return Snapshot(
          phase: .dwelling, candidatePosition: position, progress: 0, committedPosition: nil)
      }
      return Snapshot(
        phase: .dwelling, candidatePosition: center, progress: 0, committedPosition: nil)

    case .coolingDown:
      return idleSnapshot
    }
  }

  private var idleSnapshot: Snapshot {
    Snapshot(phase: .idle, candidatePosition: nil, progress: 0, committedPosition: nil)
  }
}

extension SIMD3 where Scalar == Float {
  var hasFiniteComponents: Bool { x.isFinite && y.isFinite && z.isFinite }
}
