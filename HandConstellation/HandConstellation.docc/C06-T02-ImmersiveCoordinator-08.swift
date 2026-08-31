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

    init(configuration: ConstellationConfiguration = .standard) {
        self.configuration = configuration
        renderer = ConstellationRenderer(configuration: configuration)
        dwellDetector = DwellDetector(
            dwellDuration: configuration.dwellDuration,
            stabilityRadius: configuration.stabilityRadius,
            rearmDistance: configuration.rearmDistance
        )
        fistHoldDetector = FistHoldDetector(
            holdDuration: configuration.fistHoldDuration
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
        appModel.fistGestureProgress = 0
    }

    private func cancelDwell() {
        dwellDetector.trackingLost()
        renderer.hideCursor()
    }

    private func trackingLost(appModel: AppModel) {
        cancelDwell()
        fistHoldDetector.reset()
        appModel.fistGestureProgress = 0
    }
}
