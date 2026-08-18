let fingerJoints: [(tip: HandSkeleton.JointName, knuckle: HandSkeleton.JointName)] = [
    (.indexFingerTip, .indexFingerKnuckle),
    (.middleFingerTip, .middleFingerKnuckle),
    (.ringFingerTip, .ringFingerKnuckle),
    (.littleFingerTip, .littleFingerKnuckle)
]

for names in fingerJoints {
    let tipDistance = distanceFromWrist(to: names.tip)
    let knuckleDistance = distanceFromWrist(to: names.knuckle)

    guard tipDistance / knuckleDistance < 1.45 else {
        return false
    }
}

return true
