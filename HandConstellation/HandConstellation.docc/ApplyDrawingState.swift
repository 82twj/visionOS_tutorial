private func applyDrawingState(appModel: AppModel) {
    guard appliedDrawingState != appModel.drawingState else { return }

    appliedDrawingState = appModel.drawingState
    dwellDetector.trackingLost()
    renderer.hideCursor()

    if !appModel.isDrawingEnabled {
        constellationModel.finishCurrentConstellation()
    }
}
