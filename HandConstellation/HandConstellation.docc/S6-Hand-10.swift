import ARKit
import Foundation
import simd

enum HandTrackingServiceError: Error {
  case unsupported
  case authorizationDenied
}

@MainActor
final class HandTrackingService {
  let provider = HandTrackingProvider()
  private let session = ARKitSession()

  func start() async throws {
    guard HandTrackingProvider.isSupported else { throw HandTrackingServiceError.unsupported }
    var authorization =
      await session.queryAuthorization(for: [.handTracking])[.handTracking] ?? .notDetermined
    if authorization == .notDetermined {
      authorization =
        await session.requestAuthorization(for: [.handTracking])[.handTracking] ?? .denied
    }
    guard authorization == .allowed else { throw HandTrackingServiceError.authorizationDenied }
    try await session.run([provider])
  }

  func stop() { session.stop() }

  func rightIndexFingerTipPosition(from anchor: HandAnchor) -> SIMD3<Float>? {
    guard anchor.chirality == .right, anchor.isTracked, let handSkeleton = anchor.handSkeleton
    else { return nil }
    let indexFingerTip = handSkeleton.joint(.indexFingerTip)
    guard indexFingerTip.isTracked else { return nil }
    let transform = anchor.originFromAnchorTransform * indexFingerTip.anchorFromJointTransform
    let translation = transform.columns.3
    return SIMD3<Float>(translation.x, translation.y, translation.z)
  }

  func isRightHandFist(from anchor: HandAnchor, maximumExtensionRatio: Float = 1.45) -> Bool? {
    guard anchor.chirality == .right,
      anchor.isTracked,
      let handSkeleton = anchor.handSkeleton
    else { return nil }

    let wrist = handSkeleton.joint(.wrist)
    guard wrist.isTracked else { return nil }

    let fingerJoints: [(tip: HandSkeleton.JointName, knuckle: HandSkeleton.JointName)] = [
      (.indexFingerTip, .indexFingerKnuckle),
      (.middleFingerTip, .middleFingerKnuckle),
      (.ringFingerTip, .ringFingerKnuckle),
      (.littleFingerTip, .littleFingerKnuckle),
    ]

    let wristPosition = anchorPosition(of: wrist)
    for names in fingerJoints {
      let tip = handSkeleton.joint(names.tip)
      let knuckle = handSkeleton.joint(names.knuckle)
      guard tip.isTracked, knuckle.isTracked else { return nil }

      let knuckleDistance = simd_distance(wristPosition, anchorPosition(of: knuckle))
      guard knuckleDistance > .ulpOfOne else { return nil }

      let extensionRatio = simd_distance(wristPosition, anchorPosition(of: tip)) / knuckleDistance
      if extensionRatio >= maximumExtensionRatio { return false }
    }

    return true
  }

  private func anchorPosition(of joint: HandSkeleton.Joint) -> SIMD3<Float> {
    let translation = joint.anchorFromJointTransform.columns.3
    return SIMD3<Float>(translation.x, translation.y, translation.z)
  }
}
