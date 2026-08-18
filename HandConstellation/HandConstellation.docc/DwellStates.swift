private enum State: Equatable, Sendable {
    case idle
    case dwelling(
        center: SIMD3<Float>,
        startedAt: TimeInterval
    )
    case coolingDown(
        committedPosition: SIMD3<Float>
    )
}
