import Foundation

/// Tunable values for dwell recognition and constellation rendering.
struct ConstellationConfiguration: Sendable {
    var dwellDuration: TimeInterval = 0.8
    var stabilityRadius: Float = 0.015
    var rearmDistance: Float = 0.030
    var minimumPointDistance: Float = 0.030
    var pointRadius: Float = 0.008
    var lineRadius: Float = 0.0025
    var cursorRadius: Float = 0.006
    var maximumPointCount = 100
    var fistHoldDuration: TimeInterval = 0.6
    var fistFingerExtensionRatio: Float = 1.45
}
