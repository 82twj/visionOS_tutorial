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

  func updateCursor(position: SIMD3<Float>, progress: Float) {
    cursor.position = position
    let scale = 0.75 + max(0, min(progress, 1)) * 0.75
    cursor.scale = SIMD3<Float>(repeating: scale)
    cursor.isEnabled = true
  }

  func hideCursor() { cursor.isEnabled = false }

  func addPoint(at position: SIMD3<Float>, segment: ConstellationModel.Segment?) {
    if let segment { addLine(from: segment.start, to: segment.end) }
    let point = ModelEntity(mesh: pointMesh, materials: [pointMaterial])
    point.position = position
    pointContainer.addChild(point)
  }

  private func addLine(from start: SIMD3<Float>, to end: SIMD3<Float>) {
  }
}
