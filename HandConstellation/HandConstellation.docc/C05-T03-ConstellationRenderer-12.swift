import RealityKit
import UIKit
import simd

/// Owns and updates all RealityKit entities for the constellation.
@MainActor
final class ConstellationRenderer {
    enum CursorMode {
        case point
        case closure
    }

    let rootEntity = Entity()

    private let pointContainer = Entity()
    private let lineContainer = Entity()
    private let guidanceContainer = Entity()
    private let cursor: ModelEntity
    private let closureTarget: ModelEntity
    private let pointMesh: MeshResource
    private let pointMaterial: SimpleMaterial
    private let lineMaterial: SimpleMaterial
    private let previewLineMaterial: SimpleMaterial
    private let pointCursorMaterial: UnlitMaterial
    private let closureCursorMaterial: UnlitMaterial
    private var previewLine: ModelEntity?
    private var previewSegment: ConstellationModel.Segment?

    init(configuration: ConstellationConfiguration = .standard) {
        rootEntity.name = "ConstellationRoot"
        pointContainer.name = "Points"
        lineContainer.name = "Lines"
        guidanceContainer.name = "ClosureGuidance"

        pointMesh = .generateSphere(radius: configuration.pointRadius)
        pointMaterial = SimpleMaterial(
            color: UIColor(red: 1.0, green: 0.82, blue: 0.28, alpha: 1.0),
            roughness: 0.18,
            isMetallic: true
        )
        lineMaterial = SimpleMaterial(
            color: UIColor(red: 0.25, green: 0.78, blue: 1.0, alpha: 1.0),
            roughness: 0.35,
            isMetallic: false
        )
        previewLineMaterial = SimpleMaterial(
            color: UIColor(red: 0.35, green: 0.95, blue: 1.0, alpha: 0.38),
            roughness: 0.2,
            isMetallic: false
        )
        pointCursorMaterial = UnlitMaterial(
            color: UIColor(red: 1.0, green: 0.42, blue: 0.22, alpha: 0.85)
        )
        closureCursorMaterial = UnlitMaterial(
            color: UIColor(red: 0.2, green: 0.95, blue: 1.0, alpha: 0.95)
        )

        let cursorMesh = MeshResource.generateSphere(radius: configuration.cursorRadius)
        cursor = ModelEntity(mesh: cursorMesh, materials: [pointCursorMaterial])
        cursor.name = "IndexFingerCursor"
        cursor.isEnabled = false

        let closureTargetMesh = MeshResource.generateSphere(
            radius: configuration.pointRadius * 1.7
        )
        let closureTargetMaterial = UnlitMaterial(
            color: UIColor(red: 0.2, green: 0.95, blue: 1.0, alpha: 0.24)
        )
        closureTarget = ModelEntity(
            mesh: closureTargetMesh,
            materials: [closureTargetMaterial]
        )
        closureTarget.name = "FirstPointClosureTarget"
        closureTarget.isEnabled = false

        rootEntity.addChild(lineContainer)
        rootEntity.addChild(pointContainer)
        rootEntity.addChild(guidanceContainer)
        guidanceContainer.addChild(closureTarget)
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
        let baseScale: Float = mode == .closure ? 1.0 : 0.75
        let growth: Float = mode == .closure ? 0.9 : 0.75
        cursor.scale = SIMD3<Float>(repeating: baseScale + clampedProgress * growth)
        cursor.model?.materials = [
            mode == .closure ? closureCursorMaterial : pointCursorMaterial
        ]
        cursor.isEnabled = true
    }

    func hideCursor() {
        cursor.isEnabled = false
    }

    /// Highlights the reusable first point and optionally previews the closing segment.
    func showClosureGuidance(
        firstPoint: SIMD3<Float>,
        lastPoint: SIMD3<Float>,
        progress: Float,
        showsPreview: Bool
    ) {
        closureTarget.position = firstPoint
        let clampedProgress = max(0, min(progress, 1))
        let scale: Float = showsPreview ? 1.0 + clampedProgress * 0.65 : 1.0
        closureTarget.scale = SIMD3<Float>(repeating: scale)
        closureTarget.isEnabled = true

        let segment = ConstellationModel.Segment(start: lastPoint, end: firstPoint)
        guard showsPreview else {
            removePreviewLine()
            return
        }

        guard previewSegment != segment else { return }
        removePreviewLine()
        previewLine = makeLine(
            from: segment.start,
            to: segment.end,
            radius: 0.0015,
            material: previewLineMaterial
        )
        if let previewLine {
            guidanceContainer.addChild(previewLine)
            previewSegment = segment
        }
    }

    /// Keeps a shape-and-size completion cue visible until the fingertip leaves.
    func showClosureCompletion(at position: SIMD3<Float>) {
        removePreviewLine()
        closureTarget.position = position
        closureTarget.scale = SIMD3<Float>(repeating: 1.65)
        closureTarget.isEnabled = true
    }

    func hideClosureGuidance() {
        closureTarget.isEnabled = false
        closureTarget.scale = .one
        removePreviewLine()
    }

    /// Adds a rendered point and an optional segment from the previous point.
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

    /// Adds only the exact last-to-first segment; the first point already exists.
    func closeConstellation(
        with segment: ConstellationModel.Segment,
        lineRadius: Float
    ) {
        addLine(from: segment.start, to: segment.end, radius: lineRadius)
        showClosureCompletion(at: segment.end)
    }

    /// Removes all committed entities and transient guidance while preserving the cursor.
    func reset() {
        for child in Array(pointContainer.children) {
            child.removeFromParent()
        }
        for child in Array(lineContainer.children) {
            child.removeFromParent()
        }
        hideClosureGuidance()
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

    private func makeLine(
        from start: SIMD3<Float>,
        to end: SIMD3<Float>,
        radius: Float,
        material: SimpleMaterial
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
