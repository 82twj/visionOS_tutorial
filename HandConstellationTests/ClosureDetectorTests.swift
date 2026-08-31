import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class ClosureDetectorTests: XCTestCase {
    private let first = SIMD3<Float>(0, 0, 0)
    private let last = SIMD3<Float>(0.1, 0, 0)

    func testClosureIsUnavailableBeforeThreePoints() {
        var detector = makeDetector()

        let snapshot = detector.update(
            position: first,
            firstPoint: first,
            lastPoint: last,
            pointCount: 2,
            at: 0
        )

        XCTAssertEqual(snapshot.phase, .idle)
        XCTAssertNil(snapshot.targetPosition)
    }

    func testMustLeaveLatestPointBeforeClosureCanBegin() {
        var detector = makeDetector()
        detector.pointCommitted()

        let snapshot = detector.update(
            position: last,
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0
        )

        XCTAssertEqual(snapshot.phase, .available)
        XCTAssertFalse(snapshot.didCommit)
    }

    func testDwellingNearFirstPointCommitsClosure() {
        var detector = makeDetector()
        detector.pointCommitted()

        _ = detector.update(
            position: SIMD3<Float>(0.08, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0
        )
        let started = detector.update(
            position: SIMD3<Float>(0.02, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.1
        )
        let committed = detector.update(
            position: SIMD3<Float>(0.02, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.9
        )

        XCTAssertEqual(started.phase, .dwelling)
        XCTAssertEqual(started.targetPosition, first)
        XCTAssertEqual(committed.progress, 1, accuracy: 0.0001)
        XCTAssertTrue(committed.didCommit)
    }

    func testReleaseDistancePreventsBoundaryJitterFromResettingProgress() {
        var detector = makeDetector()

        _ = detector.update(
            position: SIMD3<Float>(0.08, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0
        )
        _ = detector.update(
            position: SIMD3<Float>(0.029, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.1
        )
        let withinReleaseRadius = detector.update(
            position: SIMD3<Float>(0.035, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.5
        )

        XCTAssertEqual(withinReleaseRadius.phase, .dwelling)
        XCTAssertEqual(withinReleaseRadius.progress, 0.5, accuracy: 0.0001)
    }

    func testLeavingReleaseDistanceCancelsProgress() {
        var detector = makeDetector()

        _ = detector.update(
            position: SIMD3<Float>(0.08, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0
        )
        _ = detector.update(
            position: SIMD3<Float>(0.02, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.1
        )
        let cancelled = detector.update(
            position: SIMD3<Float>(0.05, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.5
        )

        XCTAssertEqual(cancelled.phase, .available)
        XCTAssertEqual(cancelled.progress, 0)
        XCTAssertFalse(cancelled.didCommit)
    }

    func testTrackingLossCancelsClosureProgress() {
        var detector = makeDetector()

        _ = detector.update(
            position: SIMD3<Float>(0.08, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0
        )
        _ = detector.update(
            position: SIMD3<Float>(0.02, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 0.1
        )
        detector.trackingLost()
        let restarted = detector.update(
            position: SIMD3<Float>(0.02, 0, 0),
            firstPoint: first,
            lastPoint: last,
            pointCount: 3,
            at: 1.0
        )

        XCTAssertEqual(restarted.progress, 0)
        XCTAssertFalse(restarted.didCommit)
    }

    private func makeDetector() -> ClosureDetector {
        ClosureDetector(
            dwellDuration: 0.8,
            snapDistance: 0.03,
            releaseDistance: 0.04,
            departureDistance: 0.015
        )
    }
}
