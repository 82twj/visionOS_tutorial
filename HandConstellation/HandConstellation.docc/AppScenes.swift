WindowGroup {
    ControlView()
        .environment(appModel)
}

ImmersiveSpace(id: AppModel.immersiveSpaceID) {
    ImmersiveView()
        .environment(appModel)
}
.immersionStyle(selection: .constant(.mixed), in: .mixed)
