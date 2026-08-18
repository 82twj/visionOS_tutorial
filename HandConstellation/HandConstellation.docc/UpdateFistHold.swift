switch state {
case .ready:
    state = .holding(startedAt: timestamp)

case .holding(let startedAt):
    let elapsed = timestamp - startedAt
    guard elapsed >= holdDuration else { break }

    state = .waitingForRelease
    didToggle = true

case .waitingForRelease:
    break
}
