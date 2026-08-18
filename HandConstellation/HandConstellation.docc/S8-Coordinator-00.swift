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
}
