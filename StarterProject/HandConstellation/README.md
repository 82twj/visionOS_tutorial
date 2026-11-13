# Hand Constellation 스타터 프로젝트

Hand Constellation 튜토리얼을 따라 하기 위한 시작 프로젝트입니다. `HandConstellation.xcodeproj`를 Xcode 16 이상에서 열면 바로 빌드할 수 있고, Simulator에서 실행하면 제어창이 대기 상태(그리기 꺼짐, 별자리·점·선 0개)로 뜹니다.

## 파일 구성

| 파일 | 지금 상태 | 채우는 곳 |
| --- | --- | --- |
| `AppModel.swift`, `ControlView.swift`, `ConstellationConfiguration.swift`, `ConstellationModel.swift`, `ExistingPointConnectionDetector.swift` | 완성본 | 고치지 않고 읽기만 합니다 |
| `Info.plist` | 장면 설정만 있고 손 추적 권한 설명은 없음 | Chapter 1 |
| `HandTrackingService.swift` | `import Foundation`만 있음 | Chapter 2 |
| `DwellDetector.swift` | 상태 타입, 기준값, `init`, 보조 메서드, `hasFiniteComponents`가 있고 `update(position:at:)`만 없음 | Chapter 3 |
| `ConstellationRenderer.swift` | `import Foundation`만 있음 | Chapter 3 |
| `ImmersiveCoordinator.swift`, `ImmersiveView.swift` | `import Foundation`만 있음 | Chapter 4 |
| `HandConstellationApp.swift` | 제어창 `WindowGroup`만 있음 | Chapter 4에서 `ImmersiveSpace` 추가 |

## 기기에서 실행할 때

프로젝트에는 개발 팀이 지정되어 있지 않습니다. Simulator에서는 그대로 실행되고, Apple Vision Pro에 설치할 때는 HandConstellation target의 **Signing & Capabilities**에서 Team을 고르고 필요하면 Bundle Identifier(`com.example.HandConstellation`)를 내 것으로 바꿉니다. 자세한 순서는 Chapter 5에 있습니다.
