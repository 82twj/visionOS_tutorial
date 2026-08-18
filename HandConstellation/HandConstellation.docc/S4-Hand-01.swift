import ARKit
import Foundation
import simd

enum HandTrackingServiceError: Error {
  case unsupported
  case authorizationDenied
}
