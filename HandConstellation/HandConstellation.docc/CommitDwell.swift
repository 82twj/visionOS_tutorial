let elapsed = max(0, timestamp - startedAt)
let progress = Float(min(1, elapsed / dwellDuration))

guard elapsed >= dwellDuration else {
    return Snapshot(
        phase: .dwelling,
        candidatePosition: center,
        progress: progress,
        committedPosition: nil
    )
}

state = .coolingDown(committedPosition: center)
return Snapshot(
    phase: .coolingDown,
    candidatePosition: center,
    progress: 1,
    committedPosition: center
)
