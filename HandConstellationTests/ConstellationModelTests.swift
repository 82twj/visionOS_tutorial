import XCTest
#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif

final class ConstellationModelTests: XCTestCase {
    func testFirstPointCreatesOneNodeWithoutEdge() {
        var model = makeModel()
        let point = SIMD3<Float>(0, 0, -0.5)

        let result = model.addPoint(point)

        XCTAssertEqual(result, .added(position: point, segment: nil))
        XCTAssertEqual(model.pointCount, 1)
        XCTAssertEqual(model.edgeCount, 0)
    }

    func testNewPointConnectsFromActiveNode() {
        var model = makeModel()
        let first = SIMD3<Float>(0, 0, 0)
        let second = SIMD3<Float>(0.1, 0, 0)

        _ = model.addPoint(first)
        let result = model.addPoint(second)

        XCTAssertEqual(
            result,
            .added(position: second, segment: .init(start: first, end: second))
        )
        XCTAssertEqual(model.edgeCount, 1)
        XCTAssertEqual(model.currentActivePosition, second)
    }

    func testConnectionTargetsIncludeEveryExistingNodeExceptActiveNode() {
        var model = makeModel()
        let points = makeFourPoints(in: &model)

        let targets = model.connectionTargets

        XCTAssertEqual(targets.map(\.position), Array(points.dropLast()))
        XCTAssertEqual(targets.filter(\.isAlreadyConnected).map(\.position), [points[2]])
    }

    func testConnectingToExistingNodeAddsEdgeWithoutPoint() {
        var model = makeModel()
        let points = makeFourPoints(in: &model)
        let target = model.connectionTargets.first { $0.position == points[1] }!
        let previousPointCount = model.pointCount
        let previousEdgeCount = model.edgeCount

        let result = model.connectCurrentNode(to: target.nodeID)

        XCTAssertEqual(
            result,
            .connected(
                targetPosition: points[1],
                segment: .init(start: points[3], end: points[1])
            )
        )
        XCTAssertEqual(model.pointCount, previousPointCount)
        XCTAssertEqual(model.edgeCount, previousEdgeCount + 1)
        XCTAssertEqual(model.currentActivePosition, points[1])
        XCTAssertTrue(model.constellations[0].hasCycle)
    }

    func testNewPointAfterConnectionStartsFromConnectedNode() {
        var model = makeModel()
        let points = makeFourPoints(in: &model)
        let target = model.connectionTargets.first { $0.position == points[1] }!
        _ = model.connectCurrentNode(to: target.nodeID)
        let next = SIMD3<Float>(0.2, 0.2, 0)

        let result = model.addPoint(next)

        XCTAssertEqual(
            result,
            .added(position: next, segment: .init(start: points[1], end: next))
        )
    }

    func testAlreadyConnectedEdgeIsRejectedInEitherDirection() {
        var model = makeModel()
        let first = SIMD3<Float>(0, 0, 0)
        _ = model.addPoint(first)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))
        let target = model.connectionTargets.first { $0.position == first }!

        let result = model.connectCurrentNode(to: target.nodeID)

        XCTAssertEqual(result, .rejectedAlreadyConnected)
        XCTAssertEqual(model.edgeCount, 1)
    }

    func testUnknownNodeCannotBeConnected() {
        var model = makeModel()
        _ = model.addPoint(.zero)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))

        XCTAssertEqual(
            model.connectCurrentNode(to: 999),
            .rejectedTargetUnavailable
        )
    }

    func testFinishingGraphMakesNextPointStartSeparateConstellation() {
        var model = makeModel()
        _ = model.addPoint(.zero)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))
        model.finishCurrentConstellation()
        let next = SIMD3<Float>(0.2, 0, 0)

        let result = model.addPoint(next)

        XCTAssertEqual(result, .added(position: next, segment: nil))
        XCTAssertEqual(model.constellationCount, 2)
    }

    func testRejectsPointNearAnyNodeInCurrentConstellation() {
        var model = makeModel()
        _ = model.addPoint(.zero)
        _ = model.addPoint(SIMD3<Float>(0.1, 0, 0))

        XCTAssertEqual(
            model.addPoint(SIMD3<Float>(0.01, 0, 0)),
            .rejectedTooClose
        )
    }

    func testExistingPointConnectionWorksAtPointLimit() {
        var model = ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 4)
        let points = makeFourPoints(in: &model)
        let target = model.connectionTargets.first { $0.position == points[1] }!

        XCTAssertEqual(
            model.connectCurrentNode(to: target.nodeID),
            .connected(
                targetPosition: points[1],
                segment: .init(start: points[3], end: points[1])
            )
        )
    }

    func testResetRemovesGraphsAndRestartsNodeIDs() {
        var model = makeModel()
        _ = model.addPoint(.zero)
        model.reset()
        _ = model.addPoint(SIMD3<Float>(0.2, 0, 0))

        XCTAssertEqual(model.pointCount, 1)
        XCTAssertEqual(model.edgeCount, 0)
        XCTAssertEqual(model.constellations[0].nodes[0].id, 0)
    }

    private func makeModel() -> ConstellationModel {
        ConstellationModel(minimumPointDistance: 0.03, maximumPointCount: 10)
    }

    @discardableResult
    private func makeFourPoints(
        in model: inout ConstellationModel
    ) -> [SIMD3<Float>] {
        let points = [
            SIMD3<Float>(0, 0, 0),
            SIMD3<Float>(0.1, 0, 0),
            SIMD3<Float>(0.1, 0.1, 0),
            SIMD3<Float>(0, 0.1, 0)
        ]
        for point in points {
            _ = model.addPoint(point)
        }
        return points
    }
}
