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

            HStack(spacing: 12) {
                Label(
                    "별자리 \(appModel.constellationCount)개 · 점 \(appModel.pointCount)개 · 선 \(appModel.edgeCount)개",
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

            VStack(alignment: .leading, spacing: 8) {
                Label(appModel.drawingGuidance.message, systemImage: guidanceSymbol)
                    .foregroundStyle(guidanceColor)

                if let progress = appModel.drawingGuidance.progress {
                    ProgressView("기존 점에 연결 중", value: Double(progress))
                }
            }
            .font(.callout)
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .glassBackgroundEffect()

            Label(drawingStatusLabel, systemImage: drawingStatusSymbol)
                .foregroundStyle(drawingStatusColor)

            HStack(spacing: 12) {
                Button {
                    if appModel.immersiveSpaceState == .open {
                        appModel.setDrawingEnabled(false)
                    }
                    Task { await toggleImmersiveSpace() }
                } label: {
                    Label(primaryButtonTitle, systemImage: primaryButtonSymbol)
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(appModel.isTransitioning)

                Button {
                    appModel.toggleDrawing()
                } label: {
                    Label(drawingButtonTitle, systemImage: drawingButtonSymbol)
                }
                .buttonStyle(.borderedProminent)
                .tint(appModel.isDrawingEnabled ? .orange : .green)
                .disabled(
                    appModel.immersiveSpaceState != .open
                        || appModel.trackingStatus != .tracking
                )

                Button(role: .destructive) {
                    appModel.requestReset()
                } label: {
                    Label("초기화", systemImage: "arrow.counterclockwise")
                }
                .buttonStyle(.bordered)
                .disabled(appModel.immersiveSpaceState != .open || appModel.pointCount == 0)
            }

            Label("주변의 실제 물체와 충분한 거리를 두고, 팔이 닿는 안전한 범위에서 사용하세요.", systemImage: "hand.raised.fill")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(28)
        .frame(width: 560)
    }

    private var primaryButtonTitle: String {
        switch appModel.immersiveSpaceState {
        case .closed:
            return "별자리 그리기 시작"
        case .transitioning:
            return "전환 중"
        case .open:
            return "체험 종료"
        }
    }

    private var primaryButtonSymbol: String {
        appModel.immersiveSpaceState == .open ? "xmark" : "vision.pro"
    }

    private var drawingButtonTitle: String {
        appModel.isDrawingEnabled ? "그리기 끄기" : "그리기 켜기"
    }

    private var drawingButtonSymbol: String {
        appModel.isDrawingEnabled ? "pause.fill" : "play.fill"
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

    private var guidanceSymbol: String {
        switch appModel.drawingGuidance {
        case .inactive:
            return "pause.circle"
        case .placeFirstPoint, .placeNextPoint:
            return "hand.point.up.left.fill"
        case .connecting:
            return "point.3.connected.trianglepath.dotted"
        case .connected:
            return "checkmark.circle.fill"
        case .alreadyConnected, .tooClose:
            return "arrow.left.and.right.circle.fill"
        }
    }

    private var guidanceColor: Color {
        switch appModel.drawingGuidance {
        case .inactive:
            return .secondary
        case .placeFirstPoint, .placeNextPoint:
            return .orange
        case .connecting, .connected:
            return .primary
        case .alreadyConnected, .tooClose:
            return .secondary
        }
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

    private func toggleImmersiveSpace() async {}
}

#Preview {
    ControlView()
        .environment(AppModel())
}
