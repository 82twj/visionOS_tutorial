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
}
