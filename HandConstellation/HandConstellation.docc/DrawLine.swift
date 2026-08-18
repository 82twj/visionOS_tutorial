let offset = end - start
let length = simd_length(offset)
guard length.isFinite, length > .ulpOfOne else { return }

let mesh = MeshResource.generateCylinder(height: length, radius: radius)
let line = ModelEntity(mesh: mesh, materials: [lineMaterial])
line.position = (start + end) / 2
line.orientation = simd_quatf(
    from: SIMD3<Float>(0, 1, 0),
    to: offset / length
)
