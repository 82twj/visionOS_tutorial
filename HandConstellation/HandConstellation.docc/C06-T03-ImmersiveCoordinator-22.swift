import ARKit
import Foundation
import Observation

/// Coordinates tracking, graph editing, guidance, and rendering.
@MainActor
@Observable
final class ImmersiveCoordinator {
    let renderer: ConstellationRenderer

    private let configuration: ConstellationConfiguration
    private let handTrackingService = HandTrackingService()
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
        renderer.hideConnectionGuidance()
        appModel.drawingGuidance = .inactive
    }

    func drawingStateChanged(appModel: AppModel) {
        applyDrawingState(appModel: appModel)
    }

    func reset(appModel: AppModel) {
        dwellDetector.reset()
        connectionDetector.reset()
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyConnectedPosition = nil
        appModel.pointCount = 0
        appModel.edgeCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .tracking
        syncDrawingGuidance(appModel: appModel)
    }

    func stop(appModel: AppModel) {
        handTrackingService.stop()
        trackingLost(appModel: appModel)
        constellationModel.reset()
        renderer.reset()
        rejectedPosition = nil
        recentlyConnectedPosition = nil
        appModel.setDrawingEnabled(false)
        appliedDrawingState = .disabled
        appModel.pointCount = 0
        appModel.edgeCount = 0
        appModel.constellationCount = 0
        appModel.trackingStatus = .idle
        appModel.drawingGuidance = .inactive
    }

    private func process(anchor: HandAnchor, appModel: AppModel) {
        let timestamp = ProcessInfo.processInfo.systemUptime
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

        let targets = constellationModel.connectionTargets.map {
            ExistingPointConnectionDetector.Target(
                nodeID: $0.nodeID,
                position: $0.position,
                isAlreadyConnected: $0.isAlreadyConnected
            )
        }
        let connectionSnapshot = connectionDetector.update(
            position: position,
            activePoint: constellationModel.currentActivePosition,
            targets: targets,
            at: timestamp
        )

        switch connectionSnapshot.phase {
        case .idle, .available:
            renderer.hideConnectionGuidance()
            syncDrawingGuidance(appModel: appModel)

        case .dwelling:
            guard let target = connectionSnapshot.target,
                  let sourcePoint = constellationModel.currentActivePosition else {
                renderer.hideConnectionGuidance()
                break
            }

            dwellDetector.trackingLost()
            renderer.updateCursor(
                position: position,
                progress: connectionSnapshot.progress,
                mode: .connection
            )

            if target.isAlreadyConnected {
                connectionDetector.reset()
                rejectedPosition = target.position
                rejectionGuidance = .alreadyConnected
                renderer.showConnectionCompletion(at: target.position)
                appModel.drawingGuidance = .alreadyConnected
                return
            }

            renderer.showConnectionGuidance(
                sourcePoint: sourcePoint,
                targetPoint: target.position,
                progress: connectionSnapshot.progress
            )
            appModel.drawingGuidance = .connecting(
                progress: connectionSnapshot.progress
            )

            if connectionSnapshot.didCommit {
                connectCurrentNode(to: target.nodeID, appModel: appModel)
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
            connectionDetector.pointCommitted()
            rejectedPosition = nil
            syncCounts(appModel: appModel)
            syncDrawingGuidance(appModel: appModel)

        case .rejectedLimitReached:
            appModel.trackingStatus = .failed(
                "최대 점 개수에 도달했습니다. 초기화한 후 다시 시도해 주세요."
            )

        case .rejectedTooClose:
            rejectedPosition = committedPosition
            rejectionGuidance = .tooClose
            appModel.drawingGuidance = .tooClose

        case .rejectedInvalidPosition:
            trackingLost(appModel: appModel)

        case .connected, .rejectedAlreadyConnected, .rejectedTargetUnavailable:
            break
        }
    }

    private func connectCurrentNode(to targetNodeID: Int, appModel: AppModel) {
        switch constellationModel.connectCurrentNode(to: targetNodeID) {
        case .connected(let targetPosition, let segment):
            renderer.connectExistingPoint(
                with: segment,
                lineRadius: configuration.lineRadius
            )
            recentlyConnectedPosition = targetPosition
            rejectedPosition = nil
            dwellDetector.beginCooldown(at: targetPosition)
            connectionDetector.reset()
            syncCounts(appModel: appModel)
            appModel.drawingGuidance = .connected

        case .rejectedAlreadyConnected:
            rejectedPosition = constellationModel.connectionTargets
                .first(where: { $0.nodeID == targetNodeID })?.position
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

    private func applyDrawingState(appModel: AppModel) {
        guard appliedDrawingState != appModel.drawingState else { return }

        appliedDrawingState = appModel.drawingState
        cancelDwell()
        rejectedPosition = nil
        recentlyConnectedPosition = nil

        if appModel.isDrawingEnabled {
            syncDrawingGuidance(appModel: appModel)
        } else {
            constellationModel.finishCurrentConstellation()
            connectionDetector.reset()
            appModel.drawingGuidance = .inactive
        }
    }

    private func syncCounts(appModel: AppModel) {
        appModel.pointCount = constellationModel.pointCount
        appModel.edgeCount = constellationModel.edgeCount
        appModel.constellationCount = constellationModel.constellationCount
    }

    private func syncDrawingGuidance(appModel: AppModel) {
        guard appModel.isDrawingEnabled else {
            appModel.drawingGuidance = .inactive
            return
        }

        appModel.drawingGuidance = constellationModel.currentConstellationPoints.isEmpty
            ? .placeFirstPoint
            : .placeNextPoint
    }

    private func cancelDwell() {
        dwellDetector.trackingLost()
        connectionDetector.trackingLost()
        renderer.hideCursor()
        renderer.hideConnectionGuidance()
    }

    private func trackingLost(appModel: AppModel) {
        cancelDwell()
    }
}
