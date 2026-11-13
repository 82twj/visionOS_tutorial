import simd

/// Stores the nodes and edges that form one drawable constellation graph.
struct Constellation: Equatable, Sendable {
    struct Node: Equatable, Sendable {
        let id: Int
        let position: SIMD3<Float>
    }

    struct Edge: Equatable, Hashable, Sendable {
        let lowerNodeID: Int
        let upperNodeID: Int

        init(_ firstNodeID: Int, _ secondNodeID: Int) {
            lowerNodeID = min(firstNodeID, secondNodeID)
            upperNodeID = max(firstNodeID, secondNodeID)
        }
    }

    private(set) var nodes: [Node]
    private(set) var edges: Set<Edge> = []
    private(set) var activeNodeID: Int
    private(set) var hasCycle = false

    var points: [SIMD3<Float>] {
        nodes.map(\.position)
    }

    init(firstNode: Node) {
        nodes = [firstNode]
        activeNodeID = firstNode.id
    }

    func node(id: Int) -> Node? {
        nodes.first { $0.id == id }
    }

    func containsEdge(from firstNodeID: Int, to secondNodeID: Int) -> Bool {
        edges.contains(Edge(firstNodeID, secondNodeID))
    }

    mutating func append(_ node: Node, from sourceNodeID: Int) {
        nodes.append(node)
        edges.insert(Edge(sourceNodeID, node.id))
        activeNodeID = node.id
    }

    mutating func connectActiveNode(to targetNodeID: Int) {
        edges.insert(Edge(activeNodeID, targetNodeID))
        activeNodeID = targetNodeID
        hasCycle = true
    }
}

/// Stores constellation graphs and validates point and edge creation.
struct ConstellationModel: Sendable {
    struct Segment: Equatable, Sendable {
        let start: SIMD3<Float>
        let end: SIMD3<Float>
    }

    struct ConnectionTarget: Equatable, Sendable {
        let nodeID: Int
        let position: SIMD3<Float>
        let isAlreadyConnected: Bool
    }

    enum PointAddition: Equatable, Sendable {
        case added(position: SIMD3<Float>, segment: Segment?)
        case connected(targetPosition: SIMD3<Float>, segment: Segment)
        case rejectedTooClose
        case rejectedLimitReached
        case rejectedInvalidPosition
        case rejectedAlreadyConnected
        case rejectedTargetUnavailable
    }

    let minimumPointDistance: Float
    let maximumPointCount: Int
    private(set) var constellations: [Constellation] = []
    private var isStartingNewConstellation = true
    private var nextNodeID = 0

    var points: [SIMD3<Float>] {
        constellations.flatMap(\.points)
    }

    var pointCount: Int {
        constellations.reduce(into: 0) { $0 += $1.nodes.count }
    }

    var edgeCount: Int {
        constellations.reduce(into: 0) { $0 += $1.edges.count }
    }

    var constellationCount: Int {
        constellations.count
    }

    var currentConstellationPoints: [SIMD3<Float>] {
        currentConstellation?.points ?? []
    }

    var currentActivePosition: SIMD3<Float>? {
        guard let constellation = currentConstellation else { return nil }
        return constellation.node(id: constellation.activeNodeID)?.position
    }

    var connectionTargets: [ConnectionTarget] {
        guard let constellation = currentConstellation else { return [] }
        let activeNodeID = constellation.activeNodeID

        return constellation.nodes.compactMap { node in
            guard node.id != activeNodeID else { return nil }
            return ConnectionTarget(
                nodeID: node.id,
                position: node.position,
                isAlreadyConnected: constellation.containsEdge(
                    from: activeNodeID,
                    to: node.id
                )
            )
        }
    }

    private var currentConstellation: Constellation? {
        guard !isStartingNewConstellation else { return nil }
        return constellations.last
    }

    init(
        minimumPointDistance: Float = ConstellationConfiguration.standard.minimumPointDistance,
        maximumPointCount: Int = ConstellationConfiguration.standard.maximumPointCount
    ) {
        precondition(minimumPointDistance > 0)
        precondition(maximumPointCount > 0)
        self.minimumPointDistance = minimumPointDistance
        self.maximumPointCount = maximumPointCount
    }

    /// Adds a distinct node and connects it from the active node when one exists.
    mutating func addPoint(_ position: SIMD3<Float>) -> PointAddition {
        guard position.hasFiniteComponents else {
            return .rejectedInvalidPosition
        }

        guard pointCount < maximumPointCount else {
            return .rejectedLimitReached
        }

        if currentConstellationPoints.contains(where: {
            simd_distance($0, position) < minimumPointDistance
        }) {
            return .rejectedTooClose
        }

        let node = Constellation.Node(id: nextNodeID, position: position)
        nextNodeID += 1

        if isStartingNewConstellation {
            constellations.append(Constellation(firstNode: node))
            isStartingNewConstellation = false
            return .added(position: position, segment: nil)
        }

        guard let sourcePosition = currentActivePosition else {
            return .rejectedInvalidPosition
        }

        let index = constellations.index(before: constellations.endIndex)
        let sourceNodeID = constellations[index].activeNodeID
        constellations[index].append(node, from: sourceNodeID)

        return .added(
            position: position,
            segment: Segment(start: sourcePosition, end: position)
        )
    }

    /// Adds one edge to an existing node without duplicating that node.
    mutating func connectCurrentNode(to targetNodeID: Int) -> PointAddition {
        guard let constellation = currentConstellation,
              let sourceNode = constellation.node(id: constellation.activeNodeID),
              let targetNode = constellation.node(id: targetNodeID),
              sourceNode.id != targetNode.id else {
            return .rejectedTargetUnavailable
        }

        guard !constellation.containsEdge(from: sourceNode.id, to: targetNode.id) else {
            return .rejectedAlreadyConnected
        }

        let segment = Segment(start: sourceNode.position, end: targetNode.position)
        let index = constellations.index(before: constellations.endIndex)
        constellations[index].connectActiveNode(to: targetNode.id)

        return .connected(targetPosition: targetNode.position, segment: segment)
    }

    /// Finishes the active graph so the next point begins a separate constellation.
    mutating func finishCurrentConstellation() {
        isStartingNewConstellation = true
    }

    /// Removes every constellation, node, and edge.
    mutating func reset() {
        constellations.removeAll(keepingCapacity: true)
        isStartingNewConstellation = true
        nextNodeID = 0
    }
}
