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

    /// Runs until the immersive view task is cancelled or the ARKit sequence ends.
    func run(appModel: AppModel) async {
        appModel.trackingStatus = .requestingAuthorization

        do {
            try await handTrackingService.start()
            appModel.trackingStatus = .tracking

            for await update in handTrackingService.provider.anchorUpdates {
                guard !Task.isCancelled else { break }
                guard update.anchor.chirality == .right else { continue }
                process(anchor: update.anchor, appModel: appModel)
            }

            if !Task.isCancelled {
                appModel.trackingStatus = .idle
            }
        } catch HandTrackingServiceError.unsupported {
            appModel.trackingStatus = .unsupported
        } catch HandTrackingServiceError.authorizationDenied {
            appModel.trackingStatus = .denied
        } catch is CancellationError {
            appModel.trackingStatus = .idle
        } catch {
            appModel.trackingStatus = .failed(error.localizedDescription)
        }

        handTrackingService.stop()
        renderer.hideCursor()
        renderer.hideConnectionGuidance()
        appModel.drawingGuidance = .inactive
    }

    func drawingStateChanged(appModel: AppModel) {
        applyDrawingState(appModel: appModel)
    }

    func reset(appModel: AppModel) {
        dwellDetector.reset()
        connectionDetector.reset()
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyConnectedPosition = nil
        appModel.pointCount = 0
        appModel.edgeCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .tracking
        syncDrawingGuidance(appModel: appModel)
    }

    func stop(appModel: AppModel) {
        handTrackingService.stop()
        trackingLost(appModel: appModel)
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyConnectedPosition = nil
        appModel.setDrawingEnabled(false)
        appliedDrawingState = .disabled
        appModel.pointCount = 0
        appModel.edgeCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .idle
        appModel.drawingGuidance = .inactive
    }


    // Temporary hooks. The next tutorial implements the input pipeline.
    private func process(anchor: HandAnchor, appModel: AppModel) {}
    private func applyDrawingState(appModel: AppModel) {}
    private func syncDrawingGuidance(appModel: AppModel) {}
    private func trackingLost(appModel: AppModel) {}
}
