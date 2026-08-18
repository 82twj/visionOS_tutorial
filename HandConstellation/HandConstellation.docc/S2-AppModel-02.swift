import Observation

@MainActor
@Observable
final class AppModel {
  enum ImmersiveSpaceState: Equatable {
    case closed
    case transitioning
    case open
  }
}
