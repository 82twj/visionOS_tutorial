import RealityKit
import XCTest
@testable import HandConstellation

/// Feeds synthetic fingertip positions through the coordinator the way hand tracking does.
///
/// The script follows the Chapter 5 exercise, so the counts here are the counts the
/// control window shows on a device. Run it on the visionOS Simulator; the host-side
/// Swift package excludes this file because the coordinator needs RealityKit.
@MainActor
final class ImmersiveCoordinatorTests: XCTestCase {
    private let frameInterval: TimeInterval = 1.0 / 60.0
    private var coordinator: ImmersiveCoordinator!
    private var appModel: AppModel!
    private var timestamp: TimeInterval = 100

    // First constellation.
    private let a = SIMD3<Float>(0.00, 1.40, -0.50)
    private let b = SIMD3<Float>(0.10, 1.40, -0.50)
    private let c = SIMD3<Float>(0.10, 1.30, -0.50)
    private let d = SIMD3<Float>(0.00, 1.30, -0.50)
    // Second constellation.
    private let e = SIMD3<Float>(0.30, 1.40, -0.50)
    private let f = SIMD3<Float>(0.40, 1.40, -0.50)
    private let g = SIMD3<Float>(0.35, 1.30, -0.50)

    override func setUp() async throws {
        coordinator = ImmersiveCoordinator()
        appModel = AppModel()
        timestamp = 100
    }

    override func tearDown() async throws {
        coordinator = nil
        appModel = nil
    }

    func testDrawingScriptMatchesControlWindowCounts() {
        setDrawing(true)
        XCTAssertEqual(appModel.drawingGuidance, .placeFirstPoint)

        // A, B, C, D: four points joined by three lines.
        for point in [a, b, c, d] {
            dwell(at: point)
        }
        assertCounts(constellations: 1, points: 4, lines: 3)
        XCTAssertEqual(appModel.drawingGuidance, .placeNextPoint)

        // Back to A: a line is added, a point is not.
        dwell(at: near(a))
        assertCounts(constellations: 1, points: 4, lines: 4)
        XCTAssertEqual(appModel.drawingGuidance, .connected)

        // From A across to C.
        dwell(at: near(c))
        assertCounts(constellations: 1, points: 4, lines: 5)

        // B already has a line to C, so nothing changes.
        dwell(at: near(b))
        assertCounts(constellations: 1, points: 4, lines: 5)
        XCTAssertEqual(appModel.drawingGuidance, .alreadyConnected)

        // Drawing off and on again starts a second constellation.
        setDrawing(false)
        XCTAssertEqual(appModel.drawingGuidance, .inactive)
        setDrawing(true)
        XCTAssertEqual(appModel.drawingGuidance, .placeFirstPoint)

        for point in [e, f, g] {
            dwell(at: point)
        }
        assertCounts(constellations: 2, points: 7, lines: 7)

        // Close the second constellation at its first point.
        dwell(at: near(e))
        assertCounts(constellations: 2, points: 7, lines: 8)

        coordinator.reset(appModel: appModel)
        assertCounts(constellations: 0, points: 0, lines: 0)
        XCTAssertEqual(appModel.drawingGuidance, .placeFirstPoint)
    }

    func testPointsOfAnotherConstellationAreNotConnectionTargets() {
        setDrawing(true)
        for point in [a, b, c] {
            dwell(at: point)
        }
        setDrawing(false)
        setDrawing(true)
        dwell(at: e)
        dwell(at: f)
        assertCounts(constellations: 2, points: 5, lines: 3)

        // A belongs to the first constellation. Dwelling next to it is too close to
        // nothing in the second one, so it becomes an ordinary new point.
        dwell(at: near(a))
        assertCounts(constellations: 2, points: 6, lines: 4)
    }

    func testTurningDrawingOffCancelsADwellInProgress() {
        setDrawing(true)
        hold(a, for: 0.5)
        setDrawing(false)
        setDrawing(true)
        hold(a, for: 0.5)

        // Neither half reached 0.8 seconds on its own.
        assertCounts(constellations: 0, points: 0, lines: 0)
        XCTAssertEqual(appModel.drawingGuidance, .placeFirstPoint)
    }

    func testMovingFingertipDoesNotMakeAPoint() {
        setDrawing(true)

        // Two centimeters per frame never stays inside the 1.5 cm radius.
        for step in 0..<120 {
            feed(SIMD3<Float>(Float(step) * 0.02, 1.4, -0.5))
        }
        assertCounts(constellations: 0, points: 0, lines: 0)
    }

    func testDwellingTooCloseToAPointIsRejected() {
        setDrawing(true)
        dwell(at: a)
        dwell(at: b)

        // 2 cm from B: B is the active point, so this is not a connection, and it is
        // nearer than the 3 cm minimum, so it is not a new point either. The dwell
        // detector only rearms 3 cm away, so the fingertip leaves and comes back.
        feed(c)
        dwell(at: b + SIMD3<Float>(0, 0.02, 0))
        assertCounts(constellations: 1, points: 2, lines: 1)
        XCTAssertEqual(appModel.drawingGuidance, .tooClose)
    }

    func testStopClearsEverythingAndTurnsDrawingOff() {
        setDrawing(true)
        dwell(at: a)
        dwell(at: b)

        coordinator.stop(appModel: appModel)

        assertCounts(constellations: 0, points: 0, lines: 0)
        XCTAssertFalse(appModel.isDrawingEnabled)
        XCTAssertEqual(appModel.trackingStatus, .idle)
        XCTAssertEqual(appModel.drawingGuidance, .inactive)
    }

    #if targetEnvironment(simulator)
    func testResetKeepsTheSimulatedStatus() {
        appModel.trackingStatus = .simulated
        setDrawing(true)
        dwell(at: a)

        coordinator.reset(appModel: appModel)

        XCTAssertEqual(appModel.trackingStatus, .simulated)
    }
    #endif

    // MARK: - Synthetic input

    private func setDrawing(_ isEnabled: Bool) {
        appModel.setDrawingEnabled(isEnabled)
        coordinator.drawingStateChanged(appModel: appModel)
    }

    /// Holds the fingertip at one position for a little longer than the dwell duration.
    private func dwell(at position: SIMD3<Float>) {
        hold(position, for: ConstellationConfiguration.standard.dwellDuration + 0.1)
    }

    private func hold(_ position: SIMD3<Float>, for duration: TimeInterval) {
        for _ in 0...Int(duration / frameInterval) {
            feed(position)
        }
    }

    /// One frame, following the same order as the coordinator's hand-anchor handling.
    private func feed(_ position: SIMD3<Float>) {
        timestamp += frameInterval
        guard appModel.isDrawingEnabled else { return }
        coordinator.process(position: position, at: timestamp, appModel: appModel)
    }

    /// A position 1 cm from a point, inside the 3 cm connection distance.
    private func near(_ point: SIMD3<Float>) -> SIMD3<Float> {
        point + SIMD3<Float>(0.01, 0, 0)
    }

    private func assertCounts(
        constellations: Int,
        points: Int,
        lines: Int,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        XCTAssertEqual(appModel.constellationCount, constellations, "constellations", file: file, line: line)
        XCTAssertEqual(appModel.pointCount, points, "points", file: file, line: line)
        XCTAssertEqual(appModel.edgeCount, lines, "lines", file: file, line: line)
        XCTAssertEqual(entityCount(in: "Points"), points, "point entities", file: file, line: line)
        XCTAssertEqual(entityCount(in: "Lines"), lines, "line entities", file: file, line: line)
    }

    private func entityCount(in containerName: String) -> Int {
        coordinator.renderer.rootEntity.findEntity(named: containerName)?.children.count ?? -1
    }
}
