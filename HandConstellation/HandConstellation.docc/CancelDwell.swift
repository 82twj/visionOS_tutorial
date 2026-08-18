mutating func trackingLost() {
    state = .idle
}

private func cancelDwell() {
    dwellDetector.trackingLost()
    renderer.hideCursor()
}
