import ARKit
import Foundation
import Observation

/// Coordinates tracking, dwell recognition, domain state, guidance, and rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let configuration: ConstellationConfiguration
    private let handTrackingService = HandTrackingService()
    private var dwellDetector: DwellDetector
    private var closureDetector: ClosureDetector
    private var fistHoldDetector: FistHoldDetector
    private var constellationModel: ConstellationModel
    private var appliedDrawingState: AppModel.DrawingState = .disabled
    private var rejectedPosition: SIMD3<Float>?
    private var recentlyClosedPosition: SIMD3<Float>?

    init(configuration: ConstellationConfiguration = .standard) {
        self.configuration = configuration
        renderer = ConstellationRenderer(configuration: configuration)
        dwellDetector = DwellDetector(
            dwellDuration: configuration.dwellDuration,
            stabilityRadius: configuration.stabilityRadius,
            rearmDistance: configuration.rearmDistance
        )
        closureDetector = ClosureDetector(
            dwellDuration: configuration.dwellDuration,
            snapDistance: configuration.closureSnapDistance,
            releaseDistance: configuration.closureReleaseDistance,
            departureDistance: configuration.stabilityRadius
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
        renderer.hideClosureGuidance()
        appModel.fistGestureProgress = 0
        appModel.drawingGuidance = .inactive
    }

    func drawingStateChanged(appModel: AppModel) {
        applyDrawingState(appModel: appModel)
    }

    func reset(appModel: AppModel) {
        dwellDetector.reset()
        closureDetector.reset()
        fistHoldDetector.reset()
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyClosedPosition = nil
        appModel.pointCount = 0
        appModel.constellationCount = 0
        appModel.fistGestureProgress = 0
        appModel.trackingStatus = .tracking
        syncDrawingGuidance(appModel: appModel)
    }

    func stop(appModel: AppModel) {
        handTrackingService.stop()
        trackingLost(appModel: appModel)
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyClosedPosition = nil
        appModel.setDrawingEnabled(false)
        appliedDrawingState = .disabled
        appModel.pointCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .idle
        appModel.drawingGuidance = .inactive
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
        if keepCompletionVisible(at: position, appModel: appModel) {
            return
        }

        if keepRejectionVisible(at: position, appModel: appModel) {
            return
        }

        let currentPoints = constellationModel.currentConstellationPoints
        let closureSnapshot = closureDetector.update(
            position: position,
            firstPoint: currentPoints.first,
            lastPoint: currentPoints.last,
            pointCount: currentPoints.count,
            at: timestamp
        )

        switch closureSnapshot.phase {
        case .idle:
            renderer.hideClosureGuidance()
            syncDrawingGuidance(appModel: appModel)

        case .available:
            if let firstPoint = currentPoints.first, let lastPoint = currentPoints.last {
                renderer.showClosureGuidance(
                    firstPoint: firstPoint,
                    lastPoint: lastPoint,
                    progress: 0,
                    showsPreview: false
                )
            }
            appModel.drawingGuidance = .returnToStart

        case .dwelling:
            dwellDetector.trackingLost()
            renderer.updateCursor(
                position: position,
                progress: closureSnapshot.progress,
                mode: .closure
            )
            if let firstPoint = currentPoints.first, let lastPoint = currentPoints.last {
                renderer.showClosureGuidance(
                    firstPoint: firstPoint,
                    lastPoint: lastPoint,
                    progress: closureSnapshot.progress,
                    showsPreview: true
                )
            }
            appModel.drawingGuidance = .closing(progress: closureSnapshot.progress)

            if closureSnapshot.didCommit {
                closeCurrentConstellation(appModel: appModel)
            }
            return
        }

        let snapshot = dwellDetector.update(position: position, at: timestamp)
        renderer.updateCursor(position: position, progress: snapshot.progress)

        guard let committedPosition = snapshot.committedPosition else { return }

        switch constellationModel.addPoint(committedPosition) {
        case .added(let position, let segment):
            renderer.addPoint(
                at: position,
                segment: segment,
                lineRadius: configuration.lineRadius
            )
            closureDetector.pointCommitted()
            rejectedPosition = nil
            appModel.pointCount = constellationModel.pointCount
            appModel.constellationCount = constellationModel.constellationCount
            syncDrawingGuidance(appModel: appModel)

        case .rejectedLimitReached:
            appModel.trackingStatus = .failed(
                "최대 점 개수에 도달했습니다. 초기화한 후 다시 시도해 주세요."
            )

        case .rejectedTooClose:
            rejectedPosition = committedPosition
            appModel.drawingGuidance = .tooClose

        case .rejectedInvalidPosition:
            trackingLost(appModel: appModel)

        case .closed, .rejectedNotClosable:
            break
        }
    }

    private func closeCurrentConstellation(appModel: AppModel) {
        switch constellationModel.closeCurrentConstellation() {
        case .closed(let segment):
            renderer.closeConstellation(
                with: segment,
                lineRadius: configuration.lineRadius
            )
            recentlyClosedPosition = segment.end
            rejectedPosition = nil
            dwellDetector.beginCooldown(at: segment.end)
            closureDetector.reset()
            appModel.pointCount = constellationModel.pointCount
            appModel.constellationCount = constellationModel.constellationCount
            appModel.drawingGuidance = .closed

        case .rejectedNotClosable:
            renderer.hideClosureGuidance()
            syncDrawingGuidance(appModel: appModel)

        case .added, .rejectedTooClose, .rejectedLimitReached, .rejectedInvalidPosition:
            break
        }
    }

    private func keepCompletionVisible(
        at position: SIMD3<Float>,
        appModel: AppModel
    ) -> Bool {
        guard let recentlyClosedPosition else { return false }

        guard simd_distance(position, recentlyClosedPosition)
                < configuration.closureReleaseDistance else {
            self.recentlyClosedPosition = nil
            renderer.hideClosureGuidance()
            syncDrawingGuidance(appModel: appModel)
            return false
        }

        renderer.updateCursor(position: position, progress: 1, mode: .closure)
        renderer.showClosureCompletion(at: recentlyClosedPosition)
        appModel.drawingGuidance = .closed
        return true
    }

    private func keepRejectionVisible(
        at position: SIMD3<Float>,
        appModel: AppModel
    ) -> Bool {
        guard let rejectedPosition else { return false }

        guard simd_distance(position, rejectedPosition) < configuration.rearmDistance else {
            self.rejectedPosition = nil
            syncDrawingGuidance(appModel: appModel)
            return false
        }

        renderer.updateCursor(position: position, progress: 0)
        appModel.drawingGuidance = .tooClose
        return true
    }

    private func applyDrawingState(appModel: AppModel) {
        guard appliedDrawingState != appModel.drawingState else { return }

        appliedDrawingState = appModel.drawingState
        cancelDwell()
        rejectedPosition = nil
        recentlyClosedPosition = nil

        if appModel.isDrawingEnabled {
            syncDrawingGuidance(appModel: appModel)
        } else {
            constellationModel.finishCurrentConstellation()
            closureDetector.reset()
            appModel.drawingGuidance = .inactive
        }
    }

    private func syncDrawingGuidance(appModel: AppModel) {
        guard appModel.isDrawingEnabled else {
            appModel.drawingGuidance = .inactive
            return
        }

        switch constellationModel.currentConstellationPoints.count {
        case 0:
            appModel.drawingGuidance = .placeFirstPoint
        case 1, 2:
            appModel.drawingGuidance = .placeNextPoint
        default:
            appModel.drawingGuidance = .returnToStart
        }
    }

    private func cancelDwell() {
        dwellDetector.trackingLost()
        closureDetector.trackingLost()
        renderer.hideCursor()
        renderer.hideClosureGuidance()
    }

    private func trackingLost(appModel: AppModel) {
        cancelDwell()
        fistHoldDetector.reset()
        appModel.fistGestureProgress = 0
    }
}
