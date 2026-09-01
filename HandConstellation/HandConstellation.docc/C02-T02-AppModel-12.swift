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

    enum DrawingGuidance: Equatable {
        case inactive
        case placeFirstPoint
        case placeNextPoint
        case connecting(progress: Float)
        case connected
        case alreadyConnected
        case tooClose

        var message: String {
            switch self {
            case .inactive:
                return "그리기를 켜면 검지로 점을 만들 수 있어요."
            case .placeFirstPoint:
                return "원하는 위치에서 검지를 0.8초 머물러 첫 점을 만드세요."
            case .placeNextPoint:
                return "새 위치에 점을 만들거나 기존 점에 머물러 다시 연결하세요."
            case .connecting:
                return "기존 점에 연결 중이에요. 검지를 그대로 유지하세요."
            case .connected:
                return "기존 점에 연결됐어요. 이 점에서 계속 그릴 수 있어요."
            case .alreadyConnected:
                return "이미 연결된 점이에요. 다른 기존 점을 선택해 주세요."
            case .tooClose:
                return "기존 점과 너무 가까워요. 조금 더 이동한 뒤 머물러 주세요."
            }
        }

        var progress: Float? {
            guard case .connecting(let progress) = self else { return nil }
            return progress
        }
    }

    static let immersiveSpaceID = "ConstellationSpace"

    var immersiveSpaceState: ImmersiveSpaceState = .closed
    var trackingStatus: TrackingStatus = .idle
    var drawingState: DrawingState = .disabled
    var pointCount = 0
    var edgeCount = 0
    var constellationCount = 0
    var drawingGuidance: DrawingGuidance = .inactive
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
            return "그리기 꺼짐: 다시 시작하려면 그리기 켜기 버튼을 누르세요."
        case .unsupported:
            return "이 실행 환경에서는 ARKit 손 추적을 사용할 수 없습니다."
        case .denied:
            return "손 추적 권한이 거부되었습니다. 설정에서 권한을 허용해 주세요."
        case .failed(let message):
            return "확인이 필요합니다: \(message)"
        }
    }

    var isTransitioning: Bool {
        immersiveSpaceState == .transitioning
    }

    var isDrawingEnabled: Bool {
        drawingState == .enabled
    }

    func setDrawingEnabled(_ isEnabled: Bool) {
        drawingState = isEnabled ? .enabled : .disabled
        if !isEnabled {
            drawingGuidance = .inactive
        }
    }

    func toggleDrawing() {
        setDrawingEnabled(!isDrawingEnabled)
    }

    /// Requests that the immersive renderer remove every committed point and line.
    func requestReset() {
        resetGeneration += 1
        pointCount = 0
        edgeCount = 0
        constellationCount = 0
        drawingGuidance = isDrawingEnabled ? .placeFirstPoint : .inactive
    }
}
