func updateCursor(position: SIMD3<Float>, progress: Float) {
    cursor.position = position

    let clampedProgress = max(0, min(progress, 1))
    let scale = 0.75 + clampedProgress * 0.75
    cursor.scale = SIMD3<Float>(repeating: scale)
    cursor.isEnabled = true
}
