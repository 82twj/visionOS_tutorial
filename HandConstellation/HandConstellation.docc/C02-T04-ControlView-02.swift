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

            Text("검지를 머물러 점을 만들고, 원하는 기존 점에 다시 연결해 자유롭게 별자리를 그려 보세요.")
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)

            VStack(alignment: .leading, spacing: 10) {
                Label("그리는 방법", systemImage: "questionmark.circle.fill")
                    .font(.headline)
                Label("0.8초 머물러 점 만들기", systemImage: "1.circle.fill")
                Label("다음 점을 위해 3cm 이상 이동하기", systemImage: "2.circle.fill")
                Label("기존 점에 머물러 선 다시 연결하기", systemImage: "3.circle.fill")
            }
            .font(.callout)
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .glassBackgroundEffect()

            Label("주변의 실제 물체와 충분한 거리를 두고, 팔이 닿는 안전한 범위에서 사용하세요.", systemImage: "hand.raised.fill")
                .font(.footnote)
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
