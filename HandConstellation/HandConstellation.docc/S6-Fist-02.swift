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
}
