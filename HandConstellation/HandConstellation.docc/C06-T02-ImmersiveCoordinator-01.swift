import ARKit
import Foundation
import Observation

/// Coordinates tracking, graph editing, guidance, and rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let configuration: ConstellationConfiguration
    private let handTrackingService = HandTrackingService()
    private var dwellDetector: DwellDetector
    private var connectionDetector: ExistingPointConnectionDetector
    private var constellationModel: ConstellationModel
    private var appliedDrawingState: AppModel.DrawingState = .disabled
    private var rejectedPosition: SIMD3<Float>?
    private var rejectionGuidance: AppModel.DrawingGuidance = .tooClose
    private var recentlyConnectedPosition: SIMD3<Float>?

    init(configuration: ConstellationConfiguration = .standard) {
        self.configuration = configuration
        renderer = ConstellationRenderer(configuration: configuration)
        dwellDetector = DwellDetector(
            dwellDuration: configuration.dwellDuration,
            stabilityRadius: configuration.stabilityRadius,
            rearmDistance: configuration.rearmDistance
        )
        connectionDetector = ExistingPointConnectionDetector(
            dwellDuration: configuration.dwellDuration,
            snapDistance: configuration.connectionSnapDistance,
            releaseDistance: configuration.connectionReleaseDistance,
            departureDistance: configuration.rearmDistance
        )
        constellationModel = ConstellationModel(
            minimumPointDistance: configuration.minimumPointDistance,
            maximumPointCount: configuration.maximumPointCount
        )
    }
}
