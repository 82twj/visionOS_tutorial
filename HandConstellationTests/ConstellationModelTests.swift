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
        XCTAssertEqual(model.constellations, [[first, second], [third]])
    }

    func testRejectsPointThatIsTooClose() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)

        _ = model.addPoint(.zero)
        let result = model.addPoint(SIMD3<Float>(0.01, 0, 0))

        XCTAssertEqual(result, .rejectedTooClose)
        XCTAssertEqual(model.points.count, 1)
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
