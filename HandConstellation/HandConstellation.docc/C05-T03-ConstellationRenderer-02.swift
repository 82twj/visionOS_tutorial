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
}
