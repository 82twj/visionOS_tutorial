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

    switch state {
    case .ready:
      state = .holding(startedAt: timestamp)
      return Snapshot(phase: .holding, progress: 0, didToggle: false)

    case .holding(let startedAt):
      let elapsed = max(0, timestamp - startedAt)
      let progress = Float(min(1, elapsed / holdDuration))
      guard elapsed >= holdDuration else {
        return Snapshot(phase: .holding, progress: progress, didToggle: false)
      }
      return readySnapshot

    case .waitingForRelease:
      return readySnapshot
    }
  }

  mutating func reset() {
    state = .ready
  }

  private var readySnapshot: Snapshot {
    Snapshot(phase: .ready, progress: 0, didToggle: false)
  }
}
