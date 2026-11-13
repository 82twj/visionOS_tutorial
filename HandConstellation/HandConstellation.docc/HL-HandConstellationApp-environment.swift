import SwiftUI

/// The entry point for the hand-tracked constellation experience.
@main
struct HandConstellationApp: App {

    var body: some Scene {
        WindowGroup {
            ControlView()
        }
        .windowResizability(.contentSize)
    }
}
