import Foundation

struct FistHoldDetector {
  enum Phase: Equatable {
    case ready
    case holding
    case waitingForRelease
  }
  struct Snapshot: Equatable {
    let phase: Phase
    let progress: Float
    let didToggle: Bool
  }
  private enum State: Equatable {
    case ready
    case holding(startedAt: TimeInterval)
    case waitingForRelease
  }

  let holdDuration: TimeInterval
  private var state: State = .ready

  init(holdDuration: TimeInterval = 0.6) {
    self.holdDuration = holdDuration
  }

  mutating func update(isFist: Bool, at timestamp: TimeInterval) -> Snapshot {
    guard timestamp.isFinite else {
      reset()
      return readySnapshot
    }

    guard isFist else {
      state = .ready
      return readySnapshot
    }

    return readySnapshot
  }

  mutating func reset() {
    state = .ready
  }

  private var readySnapshot: Snapshot {
    Snapshot(phase: .ready, progress: 0, didToggle: false)
  }
}
