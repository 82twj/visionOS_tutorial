import ARKit
import Foundation
import Observation

@MainActor
@Observable
final class ImmersiveCoordinator {
  let renderer: ConstellationRenderer
  private let handTrackingService = HandTrackingService()
  private var dwellDetector = DwellDetector()
  private var fistHoldDetector = FistHoldDetector()
  private var constellationModel = ConstellationModel()
  private var appliedDrawingState: AppModel.DrawingState = .disabled

  init() {
    renderer = ConstellationRenderer()
  }

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
    } catch HandTrackingServiceError.unsupported {
      appModel.trackingStatus = .unsupported
    } catch HandTrackingServiceError.authorizationDenied {
      appModel.trackingStatus = .denied
    } catch {
      appModel.trackingStatus = .failed(error.localizedDescription)
    }

    handTrackingService.stop()
    renderer.hideCursor()
  }
}
