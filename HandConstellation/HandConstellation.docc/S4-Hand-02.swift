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
}
