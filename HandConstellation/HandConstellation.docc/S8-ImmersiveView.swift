import RealityKit
import SwiftUI

struct ImmersiveView: View {
  @Environment(AppModel.self) private var appModel
  @State private var coordinator = ImmersiveCoordinator()

  var body: some View {
    RealityView { content in
      content.add(coordinator.renderer.rootEntity)
    }
    .task {
      await coordinator.run(appModel: appModel)
    }
    .onChange(of: appModel.resetGeneration) {
      coordinator.reset(appModel: appModel)
    }
    .onChange(of: appModel.drawingState) {
      coordinator.drawingStateChanged(appModel: appModel)
    }
    .onDisappear {
      coordinator.stop(appModel: appModel)
      appModel.immersiveSpaceState = .closed
    }
  }
}
