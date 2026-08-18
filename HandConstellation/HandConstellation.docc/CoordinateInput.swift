let snapshot = dwellDetector.update(
    position: position,
    at: ProcessInfo.processInfo.systemUptime
)
renderer.updateCursor(position: position, progress: snapshot.progress)

if let committedPosition = snapshot.committedPosition {
    let addition = constellationModel.addPoint(committedPosition)
    // addition의 점과 선택적 선분을 RealityKit 장면에 반영합니다.
}
