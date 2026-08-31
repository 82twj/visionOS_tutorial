import ARKit
import Foundation
import simd

enum HandTrackingServiceError: LocalizedError {
    case unsupported
    case authorizationDenied

    var errorDescription: String? {
        switch self {
        case .unsupported:
            return "이 기기 또는 실행 환경이 손 추적을 지원하지 않습니다."
        case .authorizationDenied:
            return "손 추적 권한이 허용되지 않았습니다."
        }
    }
}

/// Starts ARKit hand tracking and converts right-index anchors into world positions.
@MainActor
final class HandTrackingService {
    let provider = HandTrackingProvider()
    private let session = ARKitSession()

    func start() async throws {
        guard HandTrackingProvider.isSupported else {
            throw HandTrackingServiceError.unsupported
        }
    }
}
