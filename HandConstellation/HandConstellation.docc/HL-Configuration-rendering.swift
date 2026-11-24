import Foundation

/// Tunable values for dwell recognition and constellation rendering.
struct ConstellationConfiguration: Sendable {
    var dwellDuration: TimeInterval = 0.8
    var stabilityRadius: Float = 0.015
    var rearmDistance: Float = 0.030
    var connectionSnapDistance: Float = 0.030
    var connectionReleaseDistance: Float = 0.040
    var minimumPointDistance: Float = 0.030
    var maximumPointCount = 100
    static let standard = ConstellationConfiguration()
}
