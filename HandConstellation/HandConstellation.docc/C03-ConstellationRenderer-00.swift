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

    // 기존 점 연결 안내에 쓰는 엔티티와 재질입니다. 스타터 프로젝트가 제공합니다.
    private let guidanceContainer = Entity()
    private let connectionTarget = ModelEntity()
    private let previewLineMaterial = UnlitMaterial(color: UIColor.white.withAlphaComponent(0.35))
    private var previewLine: ModelEntity?
    private var previewSegment: ConstellationModel.Segment?

    init(configuration: ConstellationConfiguration = .standard) {
        // Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.

        prepareConnectionGuidance(pointRadius: configuration.pointRadius)
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
    /// Highlights one locked existing point and previews the prospective edge.
    func showConnectionGuidance(
        sourcePoint: SIMD3<Float>,
        targetPoint: SIMD3<Float>,
        progress: Float
    ) {
        connectionTarget.position = targetPoint
        let clampedProgress = max(0, min(progress, 1))
        connectionTarget.scale = SIMD3<Float>(repeating: 1.0 + clampedProgress * 0.6)
        connectionTarget.isEnabled = true

        let segment = ConstellationModel.Segment(start: sourcePoint, end: targetPoint)
        guard previewSegment != segment else { return }
        removePreviewLine()
        previewLine = makeLine(
            from: segment.start,
            to: segment.end,
            radius: 0.001,
            material: previewLineMaterial
        )
        if let previewLine {
            guidanceContainer.addChild(previewLine)
            previewSegment = segment
        }
    }

    /// Keeps a white shape-and-size completion cue visible until the fingertip leaves.
    func showConnectionCompletion(at position: SIMD3<Float>) {
        removePreviewLine()
        connectionTarget.position = position
        connectionTarget.scale = SIMD3<Float>(repeating: 1.6)
        connectionTarget.isEnabled = true
    }

    func hideConnectionGuidance() {
        connectionTarget.isEnabled = false
        connectionTarget.scale = .one
        removePreviewLine()
    }

    /// Gives the highlight sphere its shape and adds the guidance entities to the tree.
    private func prepareConnectionGuidance(pointRadius: Float) {
        let targetMesh = MeshResource.generateSphere(radius: pointRadius * 1.65)
        let targetMaterial = UnlitMaterial(color: UIColor.white.withAlphaComponent(0.18))
        connectionTarget.model = ModelComponent(mesh: targetMesh, materials: [targetMaterial])
        connectionTarget.name = "ExistingPointConnectionTarget"
        connectionTarget.isEnabled = false

        guidanceContainer.name = "ConnectionGuidance"
        guidanceContainer.addChild(connectionTarget)
        rootEntity.addChild(guidanceContainer)
    }

    private func removePreviewLine() {
        previewLine?.removeFromParent()
        previewLine = nil
        previewSegment = nil
    }
}
