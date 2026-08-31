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

            HStack(spacing: 12) {
                Label(
                    "별자리 \(appModel.constellationCount)개 · 점 \(appModel.pointCount)개",
                    systemImage: "circle.grid.cross"
                )
                Spacer()
                Label(statusLabel, systemImage: statusSymbol)
                    .foregroundStyle(statusColor)
            }
            .font(.headline)
            .padding()
            .glassBackgroundEffect()

            Text(appModel.statusMessage)
                .font(.callout)
                .foregroundStyle(.secondary)
        }
        .padding(28)
        .frame(width: 560)
    }

    private var statusLabel: String {
        switch appModel.trackingStatus {
        case .tracking:
            return "추적 중"
        case .requestingAuthorization:
            return "권한 확인 중"
        case .unsupported, .denied, .failed:
            return "확인 필요"
        case .idle:
            return "대기"
        }
    }

    private var statusSymbol: String {
        switch appModel.trackingStatus {
        case .tracking:
            return "hand.point.up.left.fill"
        case .requestingAuthorization:
            return "ellipsis.circle"
        case .unsupported, .denied, .failed:
            return "exclamationmark.triangle.fill"
        case .idle:
            return "pause.circle"
        }
    }

    private var statusColor: Color {
        switch appModel.trackingStatus {
        case .tracking:
            return .green
        case .requestingAuthorization:
            return .orange
        case .unsupported, .denied, .failed:
            return .red
        case .idle:
            return .secondary
        }
    }
}

#Preview {
    ControlView()
        .environment(AppModel())
}
