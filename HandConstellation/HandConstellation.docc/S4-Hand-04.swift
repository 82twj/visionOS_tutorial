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
    guard HandTrackingProvider.isSupported else {
      throw HandTrackingServiceError.unsupported
    }

    var authorization =
      await session.queryAuthorization(for: [.handTracking])[.handTracking]
      ?? .notDetermined
  }
}
