import ARKit
import Foundation
import Observation

/// Coordinates tracking, dwell recognition, domain state, and RealityKit rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let configuration: ConstellationConfiguration
    private let handTrackingService = HandTrackingService()
    private var dwellDetector: DwellDetector
    private var fistHoldDetector: FistHoldDetector
    private var constellationModel: ConstellationModel
    private var appliedDrawingState: AppModel.DrawingState = .disabled

    init(configuration: ConstellationConfiguration = .standard) {
        self.configuration = configuration
        renderer = ConstellationRenderer(configuration: configuration)
        dwellDetector = DwellDetector(
            dwellDuration: configuration.dwellDuration,
            stabilityRadius: configuration.stabilityRadius,
            rearmDistance: configuration.rearmDistance
        )
        fistHoldDetector = FistHoldDetector(
            holdDuration: configuration.fistHoldDuration
        )
        constellationModel = ConstellationModel(
            minimumPointDistance: configuration.minimumPointDistance,
            maximumPointCount: configuration.maximumPointCount
        )
    }

    /// Runs until the immersive view task is cancelled or the ARKit sequence ends.
    func run(appModel: AppModel) async {
        appModel.trackingStatus = .requestingAuthorization

        do {
            try await handTrackingService.start()
            appModel.trackingStatus = .tracking

            for await update in handTrackingService.provider.anchorUpdates {
                guard !Task.isCancelled else { break }

                guard update.anchor.chirality == .right else { continue }
                process(anchor: update.anchor, appModel: appModel)
            }

            if !Task.isCancelled {
                appModel.trackingStatus = .idle
            }
        } catch HandTrackingServiceError.unsupported {
            appModel.trackingStatus = .unsupported
        } catch HandTrackingServiceError.authorizationDenied {
            appModel.trackingStatus = .denied
        } catch is CancellationError {
            appModel.trackingStatus = .idle
        } catch {
            appModel.trackingStatus = .failed(error.localizedDescription)
        }

        handTrackingService.stop()
        renderer.hideCursor()
        appModel.fistGestureProgress = 0
    }

    func drawingStateChanged(appModel: AppModel) {
        applyDrawingState(appModel: appModel)
    }

    func reset(appModel: AppModel) {
        dwellDetector.reset()
        fistHoldDetector.reset()
        constellationModel.reset()
        renderer.reset()
        appModel.pointCount = 0
        appModel.constellationCount = 0
        appModel.fistGestureProgress = 0
        appModel.trackingStatus = .tracking
    }

    func stop(appModel: AppModel) {
        handTrackingService.stop()
        trackingLost(appModel: appModel)
        constellationModel.reset()
        renderer.reset()
        appModel.setDrawingEnabled(false)
        appliedDrawingState = .disabled
        appModel.pointCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .idle
    }

    private func process(anchor: HandAnchor, appModel: AppModel) {
        let timestamp = ProcessInfo.processInfo.systemUptime

        let isFist = handTrackingService.isRightHandFist(
            from: anchor,
            maximumExtensionRatio: configuration.fistFingerExtensionRatio
        )

        if let isFist {
            let fistSnapshot = fistHoldDetector.update(isFist: isFist, at: timestamp)
            appModel.fistGestureProgress = fistSnapshot.phase == .holding
                ? fistSnapshot.progress
                : 0

            if isFist {
                cancelDwell()

                if fistSnapshot.didToggle {
                    appModel.toggleDrawing()
                    applyDrawingState(appModel: appModel)
                }
                return
            }
        } else {
            fistHoldDetector.reset()
            appModel.fistGestureProgress = 0
        }

        applyDrawingState(appModel: appModel)
        guard appModel.isDrawingEnabled else {
            cancelDwell()
            return
        }

        guard let position = handTrackingService.rightIndexFingerTipPosition(from: anchor) else {
            trackingLost(appModel: appModel)
            return
        }

        process(position: position, at: timestamp, appModel: appModel)
    }

    private func process(
        position: SIMD3<Float>,
        at timestamp: TimeInterval,
        appModel: AppModel
    ) {
        let snapshot = dwellDetector.update(
            position: position,
            at: timestamp
        )
        renderer.updateCursor(position: position, progress: snapshot.progress)

        guard let committedPosition = snapshot.committedPosition else { return }

        switch constellationModel.addPoint(committedPosition) {
        case .added(let position, let segment):
            renderer.addPoint(
                at: position,
                segment: segment,
                lineRadius: configuration.lineRadius
            )
            appModel.pointCount = constellationModel.pointCount
            appModel.constellationCount = constellationModel.constellationCount
        case .rejectedLimitReached:
            appModel.trackingStatus = .failed("최대 점 개수에 도달했습니다. 초기화한 후 다시 시도해 주세요.")
        case .rejectedTooClose, .rejectedInvalidPosition:
            break
        }
    }

    private func applyDrawingState(appModel: AppModel) {
        guard appliedDrawingState != appModel.drawingState else { return }

        appliedDrawingState = appModel.drawingState
        cancelDwell()

        if !appModel.isDrawingEnabled {
            constellationModel.finishCurrentConstellation()
        }
    }

    private func cancelDwell() {
        dwellDetector.trackingLost()
        renderer.hideCursor()
    }

    private func trackingLost(appModel: AppModel) {
        cancelDwell()
        fistHoldDetector.reset()
        appModel.fistGestureProgress = 0
    }
}
