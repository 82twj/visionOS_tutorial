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

        var authorization = await session.queryAuthorization(for: [.handTracking])[.handTracking]
            ?? .notDetermined

        if authorization == .notDetermined {
            authorization = await session.requestAuthorization(for: [.handTracking])[.handTracking]
                ?? .denied
        }

        guard authorization == .allowed else {
            throw HandTrackingServiceError.authorizationDenied
        }

        try await session.run([provider])
    }

    func stop() {
        session.stop()
    }

    /// Returns the world-space position of a tracked right index fingertip.
    func rightIndexFingerTipPosition(from anchor: HandAnchor) -> SIMD3<Float>? {
        guard anchor.chirality == .right,
              anchor.isTracked,
              let handSkeleton = anchor.handSkeleton else {
            return nil
        }

        let indexFingerTip = handSkeleton.joint(.indexFingerTip)
        guard indexFingerTip.isTracked else { return nil }

        let originFromIndexFingerTip =
            anchor.originFromAnchorTransform * indexFingerTip.anchorFromJointTransform
        let translation = originFromIndexFingerTip.columns.3
        let position = SIMD3<Float>(translation.x, translation.y, translation.z)

        return position.hasFiniteComponents ? position : nil
    }

    /// Returns whether all four tracked fingers are folded toward the wrist.
    func isRightHandFist(
        from anchor: HandAnchor,
        maximumExtensionRatio: Float
    ) -> Bool? {
        guard anchor.chirality == .right,
              anchor.isTracked,
              let handSkeleton = anchor.handSkeleton else {
            return nil
        }

        let wrist = handSkeleton.joint(.wrist)
        guard wrist.isTracked else { return nil }

        let fingerJoints: [(
            tip: HandSkeleton.JointName,
            knuckle: HandSkeleton.JointName
        )] = [
            (.indexFingerTip, .indexFingerKnuckle),
            (.middleFingerTip, .middleFingerKnuckle),
            (.ringFingerTip, .ringFingerKnuckle),
            (.littleFingerTip, .littleFingerKnuckle)
        ]

        let wristPosition = anchorPosition(of: wrist)
        guard wristPosition.hasFiniteComponents else { return nil }

        for names in fingerJoints {
            let tip = handSkeleton.joint(names.tip)
            let knuckle = handSkeleton.joint(names.knuckle)
            guard tip.isTracked, knuckle.isTracked else { return nil }

            let tipPosition = anchorPosition(of: tip)
            let knucklePosition = anchorPosition(of: knuckle)
            guard tipPosition.hasFiniteComponents,
                  knucklePosition.hasFiniteComponents else {
                return nil
            }

            let knuckleDistance = simd_distance(wristPosition, knucklePosition)
            guard knuckleDistance > .ulpOfOne else { return nil }

            let extensionRatio = simd_distance(wristPosition, tipPosition) / knuckleDistance
            if extensionRatio >= maximumExtensionRatio {
                return false
            }
        }

        return true
    }

    private func anchorPosition(of joint: HandSkeleton.Joint) -> SIMD3<Float> {
        let translation = joint.anchorFromJointTransform.columns.3
        return SIMD3<Float>(translation.x, translation.y, translation.z)
    }
}
