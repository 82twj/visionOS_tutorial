import ARKit
import Foundation
import Observation

/// Coordinates tracking, graph editing, guidance, and rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let handTrackingService = HandTrackingService()
    private let configuration: ConstellationConfiguration
    private var dwellDetector: DwellDetector
    private var connectionDetector: ExistingPointConnectionDetector
    private var constellationModel: ConstellationModel
    private var appliedDrawingState: AppModel.DrawingState = .disabled
    private var rejectedPosition: SIMD3<Float>?
    private var rejectionGuidance: AppModel.DrawingGuidance = .tooClose
    private var recentlyConnectedPosition: SIMD3<Float>?

    init(configuration: ConstellationConfiguration = .standard) {
        self.configuration = configuration
        renderer = ConstellationRenderer(configuration: configuration)
        dwellDetector = DwellDetector(
            dwellDuration: configuration.dwellDuration,
            stabilityRadius: configuration.stabilityRadius,
            rearmDistance: configuration.rearmDistance
        )
        connectionDetector = ExistingPointConnectionDetector(
            dwellDuration: configuration.dwellDuration,
            snapDistance: configuration.connectionSnapDistance,
            releaseDistance: configuration.connectionReleaseDistance,
            departureDistance: configuration.rearmDistance
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
            await runWithoutHandTracking(appModel: appModel)
        } catch HandTrackingServiceError.authorizationDenied {
            appModel.trackingStatus = .denied
        } catch is CancellationError {
            appModel.trackingStatus = .idle
        } catch {
            appModel.trackingStatus = .failed(error.localizedDescription)
        }

        handTrackingService.stop()
        renderer.hideCursor()
        renderer.hideConnectionGuidance()
        appModel.drawingGuidance = .inactive
    }

    func drawingStateChanged(appModel: AppModel) {
        applyDrawingState(appModel: appModel)
    }

    /// Removes every point and line while tracking keeps running.
    func reset(appModel: AppModel) {
        dwellDetector.reset()
        connectionDetector.reset()
        constellationModel.reset()
        renderer.reset()
        clearHeldFeedback()
        syncCounts(appModel: appModel)
        syncDrawingGuidance(appModel: appModel)
        clearPointLimitFailure(appModel: appModel)
    }

    /// Turns one right-hand anchor update into this frame's fingertip position.
    private func process(anchor: HandAnchor, appModel: AppModel) {
        let timestamp = ProcessInfo.processInfo.systemUptime
        applyDrawingState(appModel: appModel)

        guard appModel.isDrawingEnabled else {
            cancelDwell()
            return
        }

        guard let position = handTrackingService.rightIndexFingerTipPosition(from: anchor) else {
            cancelDwell()
            return
        }

        process(position: position, at: timestamp, appModel: appModel)
    }

    /// Handles one fingertip position: an existing-point connection first, then a new point.
    func process(
        position: SIMD3<Float>,
        at timestamp: TimeInterval,
        appModel: AppModel
    ) {
        // Chapter 4에서 작성합니다.
    }
}

// MARK: - 보조 메서드 (스타터 프로젝트 제공)

extension ImmersiveCoordinator {
    /// The other points of the current constellation, in the form the connection detector takes.
    private var connectionTargets: [ExistingPointConnectionDetector.Target] {
        constellationModel.connectionTargets.map {
            ExistingPointConnectionDetector.Target(
                nodeID: $0.nodeID,
                position: $0.position,
                isAlreadyConnected: $0.isAlreadyConnected
            )
        }
    }

    /// Applies a drawing on/off change from the control window once.
    ///
    /// Turning drawing off finishes the current constellation, so the next point starts a new one.
    private func applyDrawingState(appModel: AppModel) {
        guard appliedDrawingState != appModel.drawingState else { return }

        appliedDrawingState = appModel.drawingState
        cancelDwell()
        clearHeldFeedback()

        if appModel.isDrawingEnabled {
            syncDrawingGuidance(appModel: appModel)
        } else {
            constellationModel.finishCurrentConstellation()
            connectionDetector.reset()
            appModel.drawingGuidance = .inactive
        }
    }

    /// Cancels any dwell in progress and hides the cursor and connection guidance.
    private func cancelDwell() {
        dwellDetector.trackingLost()
        connectionDetector.trackingLost()
        renderer.hideCursor()
        renderer.hideConnectionGuidance()
    }

    /// Keeps the completion cue until the fingertip leaves the point it just connected to.
    private func keepCompletionVisible(
        at position: SIMD3<Float>,
        appModel: AppModel
    ) -> Bool {
        guard let recentlyConnectedPosition else { return false }

        guard simd_distance(position, recentlyConnectedPosition)
                < configuration.connectionReleaseDistance else {
            self.recentlyConnectedPosition = nil
            renderer.hideConnectionGuidance()
            syncDrawingGuidance(appModel: appModel)
            return false
        }

        renderer.updateCursor(position: position, progress: 1, mode: .connection)
        renderer.showConnectionCompletion(at: recentlyConnectedPosition)
        appModel.drawingGuidance = .connected
        return true
    }

    /// Keeps the rejection message until the fingertip leaves the rejected position.
    private func keepRejectionVisible(
        at position: SIMD3<Float>,
        appModel: AppModel
    ) -> Bool {
        guard let rejectedPosition else { return false }

        guard simd_distance(position, rejectedPosition) < configuration.rearmDistance else {
            self.rejectedPosition = nil
            renderer.hideConnectionGuidance()
            syncDrawingGuidance(appModel: appModel)
            return false
        }

        renderer.updateCursor(position: position, progress: 0)
        appModel.drawingGuidance = rejectionGuidance
        return true
    }

    /// Shows the highlight, the preview line, and the progress while the fingertip stays on a target.
    private func showConnectionProgress(
        _ progress: Float,
        to target: ExistingPointConnectionDetector.Target,
        appModel: AppModel
    ) {
        guard let sourcePoint = constellationModel.currentActivePosition else { return }

        renderer.showConnectionGuidance(
            sourcePoint: sourcePoint,
            targetPoint: target.position,
            progress: progress
        )
        appModel.drawingGuidance = .connecting(progress: progress)
    }

    /// Hides the connection guidance when the fingertip is not on an existing point.
    private func hideConnectionProgress(appModel: AppModel) {
        renderer.hideConnectionGuidance()
        syncDrawingGuidance(appModel: appModel)
    }

    /// Refuses a target that already has an edge to the active point.
    private func rejectConnection(
        to target: ExistingPointConnectionDetector.Target,
        appModel: AppModel
    ) {
        connectionDetector.reset()
        rejectedPosition = target.position
        rejectionGuidance = .alreadyConnected
        renderer.showConnectionCompletion(at: target.position)
        appModel.drawingGuidance = .alreadyConnected
    }

    /// Adds the edge to the model and the scene after a connection dwell completes.
    private func commitConnection(
        to target: ExistingPointConnectionDetector.Target,
        appModel: AppModel
    ) {
        switch constellationModel.connectCurrentNode(to: target.nodeID) {
        case .connected(let targetPosition, let segment):
            renderer.connectExistingPoint(with: segment)
            recentlyConnectedPosition = targetPosition
            rejectedPosition = nil
            dwellDetector.beginCooldown(at: targetPosition)
            connectionDetector.reset()
            syncCounts(appModel: appModel)
            appModel.drawingGuidance = .connected

        case .rejectedAlreadyConnected:
            rejectedPosition = target.position
            rejectionGuidance = .alreadyConnected
            connectionDetector.reset()
            appModel.drawingGuidance = .alreadyConnected

        case .rejectedTargetUnavailable:
            renderer.hideConnectionGuidance()
            connectionDetector.reset()
            syncDrawingGuidance(appModel: appModel)

        case .added, .rejectedTooClose, .rejectedLimitReached, .rejectedInvalidPosition:
            break
        }
    }

    /// Updates the detectors and the control window after the model accepts a new point.
    private func pointAdded(appModel: AppModel) {
        connectionDetector.pointCommitted()
        rejectedPosition = nil
        syncCounts(appModel: appModel)
        syncDrawingGuidance(appModel: appModel)
    }

    /// Explains why the model refused a new point.
    private func pointRejected(
        _ rejection: ConstellationModel.PointAddition,
        at position: SIMD3<Float>,
        appModel: AppModel
    ) {
        switch rejection {
        case .rejectedTooClose:
            rejectedPosition = position
            rejectionGuidance = .tooClose
            appModel.drawingGuidance = .tooClose

        case .rejectedLimitReached:
            appModel.trackingStatus = .failed(
                "최대 점 개수에 도달했습니다. 초기화한 후 다시 시도해 주세요."
            )

        case .rejectedInvalidPosition:
            cancelDwell()

        case .added, .connected, .rejectedAlreadyConnected, .rejectedTargetUnavailable:
            break
        }
    }

    /// Forgets the positions that keep a completion cue or a rejection message visible.
    private func clearHeldFeedback() {
        rejectedPosition = nil
        recentlyConnectedPosition = nil
    }

    /// Copies the model's counts to the control window.
    private func syncCounts(appModel: AppModel) {
        appModel.pointCount = constellationModel.pointCount
        appModel.edgeCount = constellationModel.edgeCount
        appModel.constellationCount = constellationModel.constellationCount
    }

    /// Chooses the guidance sentence that matches the drawing state and the current constellation.
    private func syncDrawingGuidance(appModel: AppModel) {
        guard appModel.isDrawingEnabled else {
            appModel.drawingGuidance = .inactive
            return
        }

        appModel.drawingGuidance = constellationModel.currentConstellationPoints.isEmpty
            ? .placeFirstPoint
            : .placeNextPoint
    }

    /// Returns the status to its running value after a reset clears the point-limit message.
    private func clearPointLimitFailure(appModel: AppModel) {
        guard case .failed = appModel.trackingStatus else { return }

        #if targetEnvironment(simulator)
        appModel.trackingStatus = .simulated
        #else
        appModel.trackingStatus = .tracking
        #endif
    }

    /// Handles a runtime that has no hand tracking.
    ///
    /// In the Simulator, the input pad in the control window stands in for the fingertip
    /// until the task is cancelled. Everywhere else this only reports the missing support.
    private func runWithoutHandTracking(appModel: AppModel) async {
        #if targetEnvironment(simulator)
        appModel.trackingStatus = .simulated

        while !Task.isCancelled {
            processSimulatedFingertip(appModel: appModel)
            try? await Task.sleep(for: .milliseconds(16))
        }
        #else
        appModel.trackingStatus = .unsupported
        #endif
    }

    #if targetEnvironment(simulator)
    /// Feeds the input pad's position through the same steps as a hand anchor.
    private func processSimulatedFingertip(appModel: AppModel) {
        let timestamp = ProcessInfo.processInfo.systemUptime
        applyDrawingState(appModel: appModel)

        guard appModel.isDrawingEnabled, let position = appModel.simulatedFingertip else {
            cancelDwell()
            return
        }

        process(position: position, at: timestamp, appModel: appModel)
    }
    #endif
}
