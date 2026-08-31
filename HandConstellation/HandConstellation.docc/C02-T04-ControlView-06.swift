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

            HStack {
                Label(drawingStatusLabel, systemImage: drawingStatusSymbol)
                    .foregroundStyle(drawingStatusColor)
                Spacer()
                Text("오른손 주먹을 0.6초 유지해 전환")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            if appModel.fistGestureProgress > 0 {
                ProgressView(
                    "그리기 상태 전환 손짓 인식 중",
                    value: Double(appModel.fistGestureProgress)
                )
            }
        }
        .padding(28)
        .frame(width: 560)
    }

    private var drawingStatusLabel: String {
        appModel.isDrawingEnabled ? "그리기 켜짐" : "그리기 꺼짐"
    }

    private var drawingStatusSymbol: String {
        appModel.isDrawingEnabled ? "pencil.tip.crop.circle.fill" : "pencil.tip.crop.circle.badge.minus"
    }

    private var drawingStatusColor: Color {
        appModel.isDrawingEnabled ? .green : .secondary
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
