import SwiftUI

@main
struct HandConstellationApp: App {
  @State private var appModel = AppModel()

  var body: some Scene {
    WindowGroup {
      ControlView()
        .environment(appModel)
    }

    ImmersiveSpace(id: AppModel.immersiveSpaceID) {
      ImmersiveView()
        .environment(appModel)
    }
    .immersionStyle(selection: .constant(.mixed), in: .mixed)
  }
}
