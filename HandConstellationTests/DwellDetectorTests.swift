import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class DwellDetectorTests: XCTestCase {
    private let origin = SIMD3<Float>(0, 0, 0)

    func testDoesNotCommitBeforeDuration() {
        var detector = makeDetector()

        _ = detector.update(position: origin, at: 10.0)
        let snapshot = detector.update(position: origin, at: 10.79)

        XCTAssertEqual(snapshot.phase, .dwelling)
        XCTAssertNil(snapshot.committedPosition)
        XCTAssertEqual(snapshot.progress, 0.9875, accuracy: 0.0001)
    }

    func testCommitsExactlyOnceAfterDuration() {
        var detector = makeDetector()

        _ = detector.update(position: origin, at: 10.0)
        let committed = detector.update(position: origin, at: 10.8)
        let repeated = detector.update(position: origin, at: 12.0)

        XCTAssertEqual(committed.committedPosition, origin)
        XCTAssertEqual(committed.phase, .coolingDown)
        XCTAssertNil(repeated.committedPosition)
    }

    func testLeavingStabilityRadiusRestartsDwell() {
        var detector = makeDetector()
        let moved = SIMD3<Float>(0.02, 0, 0)

        _ = detector.update(position: origin, at: 0.0)
        _ = detector.update(position: origin, at: 0.7)
        let restarted = detector.update(position: moved, at: 0.71)
        let tooEarly = detector.update(position: moved, at: 0.81)

        XCTAssertEqual(restarted.progress, 0)
        XCTAssertNil(tooEarly.committedPosition)
    }

    func testTrackingLossCancelsCandidate() {
        var detector = makeDetector()

        _ = detector.update(position: origin, at: 0.0)
        detector.trackingLost()
        let restarted = detector.update(position: origin, at: 2.0)

        XCTAssertEqual(restarted.progress, 0)
        XCTAssertNil(restarted.committedPosition)
    }

    func testMovingFarEnoughRearmsDetector() {
        var detector = makeDetector()
        let next = SIMD3<Float>(0.04, 0, 0)

        _ = detector.update(position: origin, at: 0.0)
        _ = detector.update(position: origin, at: 0.8)
        let rearmed = detector.update(position: next, at: 0.9)
        let committed = detector.update(position: next, at: 1.7)

        XCTAssertEqual(rearmed.phase, .dwelling)
        XCTAssertEqual(committed.committedPosition, next)
    }

    private func makeDetector() -> DwellDetector {
        DwellDetector(dwellDuration: 0.8, stabilityRadius: 0.015, rearmDistance: 0.03)
    }
}
