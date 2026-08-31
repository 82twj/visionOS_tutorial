import ARKit
import Foundation
import Observation

/// Coordinates tracking, dwell recognition, domain state, and RealityKit rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer
}
