import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class ExistingPointConnectionDetectorTests: XCTestCase {
    private let active = SIMD3<Float>(0, 0, 0)

    func testIsIdleWithoutAnActivePointOrTargets() {
        var detector = makeDetector()

        let snapshot = detector.update(
            position: .zero,
            activePoint: nil,
            targets: [],
            at: 0
        )

        XCTAssertEqual(snapshot.phase, .idle)
        XCTAssertNil(snapshot.target)
    }

    func testMustLeaveActivePointBeforeSelectingTarget() {
        var detector = makeDetector()
        let target = makeTarget(id: 1, x: 0.02)

        let snapshot = detector.update(
            position: active,
            activePoint: active,
            targets: [target],
            at: 0
        )

        XCTAssertEqual(snapshot.phase, .available)
        XCTAssertNil(snapshot.target)
    }

    func testSelectsNearestTargetAndLocksItDuringDwell() {
        var detector = makeDetector()
        let first = makeTarget(id: 1, x: 0.10)
        let second = makeTarget(id: 2, x: 0.12)

        _ = detector.update(
            position: SIMD3<Float>(0.05, 0, 0),
            activePoint: active,
            targets: [first, second],
            at: 0
        )
        let selected = detector.update(
            position: SIMD3<Float>(0.105, 0, 0),
            activePoint: active,
            targets: [first, second],
            at: 0.1
        )
        let remainedLocked = detector.update(
            position: SIMD3<Float>(0.119, 0, 0),
            activePoint: active,
            targets: [first, second],
            at: 0.4
        )

        XCTAssertEqual(selected.target?.nodeID, first.nodeID)
        XCTAssertEqual(remainedLocked.target?.nodeID, first.nodeID)
    }

    func testDwellingCommitsExactlyOnce() {
        var detector = makeDetector()
        let target = makeTarget(id: 1, x: 0.10)

        _ = detector.update(
            position: SIMD3<Float>(0.05, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0
        )
        _ = detector.update(
            position: target.position,
            activePoint: active,
            targets: [target],
            at: 0.1
        )
        let committed = detector.update(
            position: target.position,
            activePoint: active,
            targets: [target],
            at: 0.9
        )
        let repeated = detector.update(
            position: target.position,
            activePoint: target.position,
            targets: [],
            at: 1.0
        )

        XCTAssertTrue(committed.didCommit)
        XCTAssertEqual(committed.progress, 1, accuracy: 0.0001)
        XCTAssertFalse(repeated.didCommit)
    }

    func testReleaseDistancePreventsBoundaryJitter() {
        var detector = makeDetector()
        let target = makeTarget(id: 1, x: 0.10)

        _ = detector.update(
            position: SIMD3<Float>(0.05, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0
        )
        _ = detector.update(
            position: SIMD3<Float>(0.129, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0.1
        )
        let jittered = detector.update(
            position: SIMD3<Float>(0.135, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0.5
        )

        XCTAssertEqual(jittered.phase, .dwelling)
        XCTAssertEqual(jittered.progress, 0.5, accuracy: 0.0001)
    }

    func testLeavingReleaseDistanceCancelsLockedTarget() {
        var detector = makeDetector()
        let target = makeTarget(id: 1, x: 0.10)

        _ = detector.update(
            position: SIMD3<Float>(0.05, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0
        )
        _ = detector.update(
            position: target.position,
            activePoint: active,
            targets: [target],
            at: 0.1
        )
        let cancelled = detector.update(
            position: SIMD3<Float>(0.15, 0, 0),
            activePoint: active,
            targets: [target],
            at: 0.5
        )

        XCTAssertEqual(cancelled.phase, .available)
        XCTAssertNil(cancelled.target)
        XCTAssertEqual(cancelled.progress, 0)
    }

    private func makeDetector() -> ExistingPointConnectionDetector {
        ExistingPointConnectionDetector(
            dwellDuration: 0.8,
            snapDistance: 0.03,
            releaseDistance: 0.04,
            departureDistance: 0.03
        )
    }

    private func makeTarget(
        id: Int,
        x: Float,
        isAlreadyConnected: Bool = false
    ) -> ExistingPointConnectionDetector.Target {
        .init(
            nodeID: id,
            position: SIMD3<Float>(x, 0, 0),
            isAlreadyConnected: isAlreadyConnected
        )
    }
}
