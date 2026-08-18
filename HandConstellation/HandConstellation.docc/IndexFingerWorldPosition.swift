let indexFingerTip = handSkeleton.joint(.indexFingerTip)
guard indexFingerTip.isTracked else { return nil }

let originFromIndexFingerTip =
    anchor.originFromAnchorTransform * indexFingerTip.anchorFromJointTransform
let translation = originFromIndexFingerTip.columns.3
let position = SIMD3<Float>(translation.x, translation.y, translation.z)
