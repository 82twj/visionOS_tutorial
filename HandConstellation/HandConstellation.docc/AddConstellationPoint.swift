let previousPoint = isStartingNewConstellation
    ? nil
    : constellations.last?.last

let segment = previousPoint.map {
    Segment(start: $0, end: position)
}

if isStartingNewConstellation {
    constellations.append([position])
    isStartingNewConstellation = false
} else {
    constellations[constellations.count - 1].append(position)
}
