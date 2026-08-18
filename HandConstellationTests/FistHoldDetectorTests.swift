import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class FistHoldDetectorTests: XCTestCase {
    func testDoesNotToggleBeforeHoldDuration() {
        var detector = FistHoldDetector(holdDuration: 0.6)

        _ = detector.update(isFist: true, at: 10.0)
        let snapshot = detector.update(isFist: true, at: 10.59)

        XCTAssertEqual(snapshot.phase, .holding)
        XCTAssertFalse(snapshot.didToggle)
        XCTAssertEqual(snapshot.progress, 0.9833, accuracy: 0.0001)
    }

    func testHeldFistTogglesExactlyOnce() {
        var detector = FistHoldDetector(holdDuration: 0.6)

        _ = detector.update(isFist: true, at: 0.0)
        let toggled = detector.update(isFist: true, at: 0.6)
        let repeated = detector.update(isFist: true, at: 1.2)

        XCTAssertTrue(toggled.didToggle)
        XCTAssertEqual(toggled.phase, .waitingForRelease)
        XCTAssertFalse(repeated.didToggle)
    }

    func testReleaseRearmsTheGesture() {
        var detector = FistHoldDetector(holdDuration: 0.6)

        _ = detector.update(isFist: true, at: 0.0)
        _ = detector.update(isFist: true, at: 0.6)
        _ = detector.update(isFist: false, at: 0.7)
        _ = detector.update(isFist: true, at: 1.0)
        let toggledAgain = detector.update(isFist: true, at: 1.6)

        XCTAssertTrue(toggledAgain.didToggle)
    }

    func testEarlyReleaseCancelsTheHold() {
        var detector = FistHoldDetector(holdDuration: 0.6)

        _ = detector.update(isFist: true, at: 0.0)
        _ = detector.update(isFist: false, at: 0.4)
        let restarted = detector.update(isFist: true, at: 1.0)

        XCTAssertEqual(restarted.progress, 0)
        XCTAssertFalse(restarted.didToggle)
    }
}
