#if targetEnvironment(simulator)
import SwiftUI

/// The rectangle in the immersive space that the Simulator input pad maps onto.
///
/// The Simulator has no hand tracking, so the pad in the control window stands in
/// for the right index fingertip. Change these values to move or resize the area.
enum SimulatorInputRegion {
    /// The center of the rectangle, in meters from the immersive space origin.
    static let center = SIMD3<Float>(-0.42, 1.55, -0.7)
    /// The width and height of the rectangle, in meters.
    static let size = SIMD2<Float>(0.45, 0.30)

    /// Converts a pad location to a position on the rectangle.
    ///
    /// `x` and `y` run from 0 to 1, measured from the pad's top-left corner.
    static func position(x: Float, y: Float) -> SIMD3<Float> {
        let clampedX = max(0, min(x, 1))
        let clampedY = max(0, min(y, 1))
        return SIMD3<Float>(
            center.x + (clampedX - 0.5) * size.x,
            center.y + (0.5 - clampedY) * size.y,
            center.z
        )
    }
}

/// A pad that reports a pressed location as the fingertip position.
struct SimulatorInputPad: View {
    @Environment(AppModel.self) private var appModel
    @State private var pressLocation: CGPoint?

    private let padWidth: CGFloat = 360

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Simulator 입력 패드", systemImage: "cursorarrow.rays")
                .font(.headline)

            pad

            Text(hint)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(20)
        .glassBackgroundEffect()
        .onDisappear(perform: release)
    }

    private var pad: some View {
        let shape = RoundedRectangle(cornerRadius: 16)
        let padHeight = padWidth * CGFloat(SimulatorInputRegion.size.y / SimulatorInputRegion.size.x)

        return ZStack(alignment: .topLeading) {
            shape.fill(.white.opacity(0.08))
            shape.strokeBorder(.white.opacity(0.35))

            if let pressLocation {
                Circle()
                    .fill(.white)
                    .frame(width: 14, height: 14)
                    .position(pressLocation)
            }
        }
        .frame(width: padWidth, height: padHeight)
        .contentShape(shape)
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { value in
                    press(at: value.location, in: CGSize(width: padWidth, height: padHeight))
                }
                .onEnded { _ in
                    release()
                }
        )
        .opacity(appModel.isDrawingEnabled ? 1 : 0.4)
        .allowsHitTesting(appModel.isDrawingEnabled)
    }

    private var hint: String {
        appModel.isDrawingEnabled
            ? "누른 채 0.8초 멈추면 그 자리에 점이 찍혀요."
            : "그리기 시작을 누르면 입력 패드를 쓸 수 있어요."
    }

    private func press(at location: CGPoint, in size: CGSize) {
        let clamped = CGPoint(
            x: max(0, min(location.x, size.width)),
            y: max(0, min(location.y, size.height))
        )
        pressLocation = clamped
        appModel.simulatedFingertip = SimulatorInputRegion.position(
            x: Float(clamped.x / size.width),
            y: Float(clamped.y / size.height)
        )
    }

    private func release() {
        pressLocation = nil
        appModel.simulatedFingertip = nil
    }
}
#endif
