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
    }
}
