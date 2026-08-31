import RealityKit
import SwiftUI

/// Hosts the RealityKit scene and binds its lifetime to hand tracking.
struct ImmersiveView: View {
    @Environment(AppModel.self) private var appModel
    @State private var coordinator = ImmersiveCoordinator()
    var body: some View {
        RealityView { content in
            content.add(coordinator.renderer.rootEntity)
        }
    }
}
