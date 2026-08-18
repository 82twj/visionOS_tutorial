import RealityKit
import UIKit
import simd

@MainActor
final class ConstellationRenderer {
  let rootEntity = Entity()
  private let pointContainer = Entity()
  private let lineContainer = Entity()
  private let cursor: ModelEntity
  private let pointMesh: MeshResource
  private let pointMaterial: SimpleMaterial
  private let lineMaterial: SimpleMaterial

  init() {
    pointMesh = .generateSphere(radius: 0.008)
    pointMaterial = SimpleMaterial(color: .yellow, roughness: 0.18, isMetallic: true)
    lineMaterial = SimpleMaterial(color: .cyan, roughness: 0.35, isMetallic: false)

    let cursorMesh = MeshResource.generateSphere(radius: 0.006)
    cursor = ModelEntity(mesh: cursorMesh, materials: [UnlitMaterial(color: .orange)])
    cursor.isEnabled = false

    rootEntity.addChild(lineContainer)
    rootEntity.addChild(pointContainer)
    rootEntity.addChild(cursor)
  }
}
