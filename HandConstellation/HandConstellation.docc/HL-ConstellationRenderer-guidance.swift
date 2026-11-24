import RealityKit
import SwiftUI
import UIKit
import simd

/// Owns and updates all RealityKit entities for the constellation.
@MainActor
final class ConstellationRenderer {
    enum CursorMode {
        case point
        case connection
    }

    let rootEntity = Entity()


    init(configuration: ConstellationConfiguration = .standard) {
        // Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.

    }

    /// Moves the fingertip cursor and grows it as dwell progress increases.
    func updateCursor(
        position: SIMD3<Float>,
        progress: Float,
        mode: CursorMode = .point
    ) {
        // Chapter 3에서 작성합니다.
    }

    func hideCursor() {
        // Chapter 3에서 작성합니다.
    }

    /// Builds a thin cylinder that spans two points.
    private func makeLine(
        from start: SIMD3<Float>,
        to end: SIMD3<Float>,
        radius: Float,
        material: UnlitMaterial
    ) -> ModelEntity? {
        // Chapter 3에서 작성합니다.
        return nil
    }

    /// Adds only an edge to an existing point; no point entity is duplicated.
    func connectExistingPoint(with segment: ConstellationModel.Segment) {
        // Chapter 3에서 작성합니다.
    }
}

// MARK: - 기존 점 연결 안내 (스타터 프로젝트 제공)

extension ConstellationRenderer {
}
