import SwiftUI

/// The window interface for opening, closing, and resetting the experience.
struct ControlView: View {
    @Environment(AppModel.self) private var appModel
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Label("Hand Constellation", systemImage: "sparkles")
                .font(.largeTitle.bold())

            Text("공간을 연 뒤 그리기를 켜고, 오른손 검지를 한 위치에 0.8초 동안 머물러 별 점을 만드세요.")
                .foregroundStyle(.secondary)
        }
        .padding(28)
        .frame(width: 560)
    }
}

#Preview {
    ControlView()
        .environment(AppModel())
}
