guard simd_distance(center, position) <= stabilityRadius else {
    state = .dwelling(center: position, startedAt: timestamp)
    return Snapshot(
        phase: .dwelling,
        candidatePosition: position,
        progress: 0,
        committedPosition: nil
    )
}

let elapsed = max(0, timestamp - startedAt)
let progress = Float(min(1, elapsed / dwellDuration))
