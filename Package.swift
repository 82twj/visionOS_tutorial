// swift-tools-version: 6.2

import PackageDescription

// This package is a host-side test harness for framework-independent logic.
// The shipping visionOS application remains HandConstellation.xcodeproj.
let package = Package(
    name: "HandConstellationCore",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        .library(name: "HandConstellationCore", targets: ["HandConstellationCore"])
    ],
    targets: [
        .target(
            name: "HandConstellationCore",
            path: "HandConstellation",
            exclude: [
                "AppModel.swift",
                "ConstellationRenderer.swift",
                "ControlView.swift",
                "HandConstellationApp.swift",
                "HandTrackingService.swift",
                "ImmersiveCoordinator.swift",
                "ImmersiveView.swift",
                "Info.plist"
            ],
            sources: [
                "ExistingPointConnectionDetector.swift",
                "ConstellationConfiguration.swift",
                "ConstellationModel.swift",
                "DwellDetector.swift"
            ]
        ),
        .testTarget(
            name: "HandConstellationCoreTests",
            dependencies: ["HandConstellationCore"],
            path: "HandConstellationTests"
        )
    ]
)
