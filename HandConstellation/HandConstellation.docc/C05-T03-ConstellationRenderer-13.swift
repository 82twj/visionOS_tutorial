import RealityKit
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

    private let pointContainer = Entity()
    private let lineContainer = Entity()
    private let guidanceContainer = Entity()
    private let cursor: ModelEntity
    private let connectionTarget: ModelEntity
    private let pointMesh: MeshResource
    private let pointMaterial: UnlitMaterial
    private let lineMaterial: UnlitMaterial
    private let previewLineMaterial: UnlitMaterial
    private let pointCursorMaterial: UnlitMaterial
    private let connectionCursorMaterial: UnlitMaterial
    private var previewLine: ModelEntity?
    private var previewSegment: ConstellationModel.Segment?

    init(configuration: ConstellationConfiguration = .standard) {
        rootEntity.name = "ConstellationRoot"
        pointContainer.name = "Points"
        lineContainer.name = "Lines"
        guidanceContainer.name = "ConnectionGuidance"

        pointMesh = .generateSphere(radius: configuration.pointRadius)
        pointMaterial = UnlitMaterial(color: UIColor.white)
        lineMaterial = UnlitMaterial(color: UIColor.white.withAlphaComponent(0.92))
        previewLineMaterial = UnlitMaterial(
            color: UIColor.white.withAlphaComponent(0.35)
        )
        pointCursorMaterial = UnlitMaterial(
            color: UIColor.white.withAlphaComponent(0.72)
        )
        connectionCursorMaterial = UnlitMaterial(color: UIColor.white)

        let cursorMesh = MeshResource.generateSphere(radius: configuration.cursorRadius)
        cursor = ModelEntity(mesh: cursorMesh, materials: [pointCursorMaterial])
        cursor.name = "IndexFingerCursor"
        cursor.isEnabled = false

        let targetMesh = MeshResource.generateSphere(radius: configuration.pointRadius * 1.65)
        let targetMaterial = UnlitMaterial(
            color: UIColor.white.withAlphaComponent(0.18)
        )
        connectionTarget = ModelEntity(mesh: targetMesh, materials: [targetMaterial])
        connectionTarget.name = "ExistingPointConnectionTarget"
        connectionTarget.isEnabled = false

        rootEntity.addChild(lineContainer)
        rootEntity.addChild(pointContainer)
        rootEntity.addChild(guidanceContainer)
        guidanceContainer.addChild(connectionTarget)
        rootEntity.addChild(cursor)
    }

    /// Moves the fingertip cursor and grows it as dwell progress increases.
    func updateCursor(
        position: SIMD3<Float>,
        progress: Float,
        mode: CursorMode = .point
    ) {
        cursor.position = position
        let clampedProgress = max(0, min(progress, 1))
        let baseScale: Float = mode == .connection ? 1.0 : 0.72
        let growth: Float = mode == .connection ? 0.85 : 0.7
        cursor.scale = SIMD3<Float>(repeating: baseScale + clampedProgress * growth)
        cursor.model?.materials = [
            mode == .connection ? connectionCursorMaterial : pointCursorMaterial
        ]
        cursor.isEnabled = true
    }

    func hideCursor() {
        cursor.isEnabled = false
    }

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

    /// Adds a rendered point and an optional segment from the active point.
    func addPoint(
        at position: SIMD3<Float>,
        segment: ConstellationModel.Segment?,
        lineRadius: Float
    ) {
        if let segment {
            addLine(from: segment.start, to: segment.end, radius: lineRadius)
        }

        let point = ModelEntity(mesh: pointMesh, materials: [pointMaterial])
        point.position = position
        pointContainer.addChild(point)
    }

    /// Adds only an edge to an existing point; no point entity is duplicated.
    func connectExistingPoint(
        with segment: ConstellationModel.Segment,
        lineRadius: Float
    ) {
        addLine(from: segment.start, to: segment.end, radius: lineRadius)
        showConnectionCompletion(at: segment.end)
    }

    /// Removes all committed entities and transient guidance while preserving the cursor.
    func reset() {
        for child in Array(pointContainer.children) {
            child.removeFromParent()
        }
        for child in Array(lineContainer.children) {
            child.removeFromParent()
        }
        hideConnectionGuidance()
        hideCursor()
    }

    private func addLine(from start: SIMD3<Float>, to end: SIMD3<Float>, radius: Float) {
        guard let line = makeLine(
            from: start,
            to: end,
            radius: radius,
            material: lineMaterial
        ) else { return }
        lineContainer.addChild(line)
    }

    private func makeLine<M: Material>(
        from start: SIMD3<Float>,
        to end: SIMD3<Float>,
        radius: Float,
        material: M
    ) -> ModelEntity? {
        let offset = end - start
        let length = simd_length(offset)
        guard length.isFinite, length > .ulpOfOne else { return nil }

        let mesh = MeshResource.generateCylinder(height: length, radius: radius)
        let line = ModelEntity(mesh: mesh, materials: [material])
        line.position = (start + end) / 2
        line.orientation = simd_quatf(
            from: SIMD3<Float>(0, 1, 0),
            to: offset / length
        )
        return line
    }

    private func removePreviewLine() {
        previewLine?.removeFromParent()
        previewLine = nil
        previewSegment = nil
    }
}
