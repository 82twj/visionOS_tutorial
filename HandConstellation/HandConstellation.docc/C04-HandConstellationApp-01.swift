import SwiftUI

/// The entry point for the hand-tracked constellation experience.
@main
struct HandConstellationApp: App {
    @State private var appModel = AppModel()

    var body: some Scene {
        WindowGroup {
            ControlView()
                .environment(appModel)
        }
        .windowResizability(.contentSize)

        ImmersiveSpace(id: AppModel.immersiveSpaceID) {
            ImmersiveView()
                .environment(appModel)
        }
        .immersionStyle(selection: .constant(.mixed), in: .mixed)
    }
}
