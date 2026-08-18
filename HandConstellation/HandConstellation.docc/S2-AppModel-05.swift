import Observation

@MainActor
@Observable
final class AppModel {
  enum ImmersiveSpaceState: Equatable {
    case closed
    case transitioning
    case open
  }

  enum TrackingStatus: Equatable {
    case idle
    case requestingAuthorization
    case tracking
    case unsupported
    case denied
    case failed(String)
  }

  enum DrawingState: Equatable {
    case disabled
    case enabled
  }

  static let immersiveSpaceID = "ConstellationSpace"

  var immersiveSpaceState: ImmersiveSpaceState = .closed
  var trackingStatus: TrackingStatus = .idle
  var drawingState: DrawingState = .disabled
}
