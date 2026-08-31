import Observation

/// Shared user-interface state for the window and immersive space.
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
    var pointCount = 0
    var constellationCount = 0
    var fistGestureProgress: Float = 0
    private(set) var resetGeneration = 0
}
