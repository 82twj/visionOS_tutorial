import ARKit
import Foundation
import Observation

/// Coordinates tracking, dwell recognition, domain state, and RealityKit rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let configuration: ConstellationConfiguration
    private let handTrackingService = HandTrackingService()
    private var dwellDetector: DwellDetector
    private var fistHoldDetector: FistHoldDetector
    private var constellationModel: ConstellationModel
    private var appliedDrawingState: AppModel.DrawingState = .disabled
}
