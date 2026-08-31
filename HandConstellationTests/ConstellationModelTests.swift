import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class ConstellationModelTests: XCTestCase {
    func testFirstPointHasNoSegment() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
        let point = SIMD3<Float>(0, 0, -0.5)

        let result = model.addPoint(point)

        XCTAssertEqual(result, .added(position: point, segment: nil))
        XCTAssertEqual(model.points, [point])
    }

    func testSecondPointCreatesSegmentFromPreviousPoint() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
        let first = SIMD3<Float>(0, 0, -0.5)
        let second = SIMD3<Float>(0.1, 0.1, -0.5)

        _ = model.addPoint(first)
        let result = model.addPoint(second)

        XCTAssertEqual(
            result,
            .added(
                position: second,
                segment: .init(start: first, end: second)
            )
        )
    }

    func testFinishingCurrentConstellationBreaksTheNextSegment() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
        let first = SIMD3<Float>(0, 0, -0.5)
        let second = SIMD3<Float>(0.1, 0, -0.5)
        let third = SIMD3<Float>(0.2, 0, -0.5)

        _ = model.addPoint(first)
        _ = model.addPoint(second)
        model.finishCurrentConstellation()
        let result = model.addPoint(third)

        XCTAssertEqual(result, .added(position: third, segment: nil))
        XCTAssertEqual(model.constellationCount, 2)
        XCTAssertEqual(model.constellations.map(\.points), [[first, second], [third]])
    }

    func testRejectsPointThatIsTooClose() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)

        _ = model.addPoint(.zero)
        let result = model.addPoint(SIMD3<Float>(0.01, 0, 0))

        XCTAssertEqual(result, .rejectedTooClose)
        XCTAssertEqual(model.points.count, 1)
    }

    func testRejectsPointNearAnyExistingPointBeforeClosureIsAvailable() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
        let first = SIMD3<Float>(0, 0, -0.5)
        let second = SIMD3<Float>(0.1, 0, -0.5)

        _ = model.addPoint(first)
        _ = model.addPoint(second)
        let result = model.addPoint(first + SIMD3<Float>(0.01, 0, 0))

        XCTAssertEqual(result, .rejectedTooClose)
        XCTAssertEqual(model.pointCount, 2)
    }

    func testClosingTriangleReusesExactFirstPointWithoutAddingAFourthPoint() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
        let first = SIMD3<Float>(0, 0, -0.5)
        let second = SIMD3<Float>(0.1, 0, -0.5)
        let third = SIMD3<Float>(0.05, 0.1, -0.5)

        _ = model.addPoint(first)
        _ = model.addPoint(second)
        _ = model.addPoint(third)
        let result = model.closeCurrentConstellation()

        XCTAssertEqual(
            result,
            .closed(segment: .init(start: third, end: first))
        )
        XCTAssertEqual(model.pointCount, 3)
        XCTAssertEqual(model.points, [first, second, third])
        XCTAssertTrue(model.constellations[0].isClosed)
    }

    func testClosingIsRejectedUntilThreeDistinctPointsExist() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)

        _ = model.addPoint(.zero)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))

        XCTAssertEqual(model.closeCurrentConstellation(), .rejectedNotClosable)
        XCTAssertFalse(model.constellations[0].isClosed)
    }

    func testPointAfterClosureStartsANewConstellationWithoutConnecting() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)

        _ = model.addPoint(.zero)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))
        _ = model.addPoint(SIMD3<Float>(0.05, 0.1, 0))
        _ = model.closeCurrentConstellation()

        let next = SIMD3<Float>(0.2, 0.2, 0)
        let result = model.addPoint(next)

        XCTAssertEqual(result, .added(position: next, segment: nil))
        XCTAssertEqual(model.constellationCount, 2)
        XCTAssertEqual(model.constellations[1].points, [next])
        XCTAssertFalse(model.constellations[1].isClosed)
    }

    func testClosureStillWorksAtMaximumPointCountBecauseItAddsNoPoint() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 3)
        let first = SIMD3<Float>(0, 0, 0)
        let third = SIMD3<Float>(0.05, 0.1, 0)

        _ = model.addPoint(first)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))
        _ = model.addPoint(third)

        XCTAssertEqual(
            model.closeCurrentConstellation(),
            .closed(segment: .init(start: third, end: first))
        )
    }

    func testRejectsPointBeyondLimit() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 1)

        _ = model.addPoint(.zero)
        let result = model.addPoint(SIMD3<Float>(0.1, 0, 0))

        XCTAssertEqual(result, .rejectedLimitReached)
    }

    func testResetRemovesAllPoints() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)

        _ = model.addPoint(.zero)
        model.reset()

        XCTAssertTrue(model.points.isEmpty)
        XCTAssertTrue(model.constellations.isEmpty)
        XCTAssertEqual(model.constellationCount, 0)
    }
}
