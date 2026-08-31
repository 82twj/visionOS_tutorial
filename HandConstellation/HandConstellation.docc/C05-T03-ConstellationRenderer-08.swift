import RealityKit
import UIKit
import simd

/// Owns and updates all RealityKit entities for the constellation.
@MainActor
final class ConstellationRenderer {
    let rootEntity = Entity()

    private let pointContainer = Entity()
    private let lineContainer = Entity()
    private let cursor: ModelEntity
    private let pointMesh: MeshResource
    private let pointMaterial: SimpleMaterial
    private let lineMaterial: SimpleMaterial

    init(configuration: ConstellationConfiguration = .standard) {
        rootEntity.name = "ConstellationRoot"
        pointContainer.name = "Points"
        lineContainer.name = "Lines"

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

        let cursorMesh = MeshResource.generateSphere(radius: configuration.cursorRadius)
        let cursorMaterial = UnlitMaterial(
            color: UIColor(red: 1.0, green: 0.42, blue: 0.22, alpha: 0.85)
        )
        cursor = ModelEntity(mesh: cursorMesh, materials: [cursorMaterial])
        cursor.name = "IndexFingerCursor"
        cursor.isEnabled = false

        rootEntity.addChild(lineContainer)
        rootEntity.addChild(pointContainer)
        rootEntity.addChild(cursor)
    }

    /// Moves the fingertip cursor and grows it as dwell progress increases.
    func updateCursor(position: SIMD3<Float>, progress: Float) {
        cursor.position = position
        let clampedProgress = max(0, min(progress, 1))
        let scale = 0.75 + clampedProgress * 0.75
        cursor.scale = SIMD3<Float>(repeating: scale)
        cursor.isEnabled = true
    }

    func hideCursor() {
        cursor.isEnabled = false
    }
}
