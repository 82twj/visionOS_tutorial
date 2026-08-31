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

    var statusMessage: String {
        switch trackingStatus {
        case .idle:
            return immersiveSpaceState == .closed ? "체험을 시작할 준비가 되었습니다." : "손 추적을 준비하고 있습니다."
        case .requestingAuthorization:
            return "손 추적 권한을 확인하고 있습니다."
        case .tracking:
            if isDrawingEnabled {
                return "그리기 켜짐: 오른손 검지를 한곳에 잠시 머물러 보세요."
            }
            return "그리기 꺼짐: 오른손 주먹을 0.6초 유지하거나 버튼으로 켜세요."
        case .unsupported:
            return "이 실행 환경에서는 ARKit 손 추적을 사용할 수 없습니다."
        case .denied:
            return "손 추적 권한이 거부되었습니다. 설정에서 권한을 허용해 주세요."
        case .failed(let message):
            return "확인이 필요합니다: \(message)"
        }
    }
}
