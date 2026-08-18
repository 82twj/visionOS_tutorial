for await update in provider.anchorUpdates {
    guard update.anchor.chirality == .right else { continue }

    if let position = rightIndexFingerTipPosition(from: update.anchor) {
        process(position: position)
    } else {
        trackingLost()
    }
}
