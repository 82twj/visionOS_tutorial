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
}
