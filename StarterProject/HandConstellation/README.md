# Hand Constellation 스타터 프로젝트

Hand Constellation 튜토리얼을 따라 하기 위한 시작 프로젝트입니다. `HandConstellation.xcodeproj`를 Xcode 16 이상에서 열면 바로 빌드됩니다. Simulator에서 실행하면 제어창이 대기 상태(그리기 꺼짐, 별자리·점·선 0개)로 뜹니다. **별자리 그리기 시작** 버튼은 Chapter 4에서 연결하기 전까지 눌러도 반응하지 않습니다.

## 파일 구성

| 파일 | 지금 상태 | 작성하는 곳 |
| --- | --- | --- |
| `AppModel.swift`, `ConstellationConfiguration.swift`, `ConstellationModel.swift`, `ExistingPointConnectionDetector.swift`, `SimulatorInputPad.swift` | 완성본 | 고치지 않고 읽기만 합니다 |
| `Info.plist` | 장면 설정만 있고 손 추적 권한 설명은 없음 | Chapter 1 |
| `HandTrackingService.swift` | `import Foundation`만 있음 | Chapter 2 |
| `DwellDetector.swift` | 상태 타입, 기준값, `init`, 보조 메서드가 있고 `update(position:at:)`만 없음 | Chapter 3 |
| `ConstellationRenderer.swift` | 기존 점 연결 안내 부분이 있음. `init`과 `updateCursor`, `hideCursor`, `makeLine`, `connectExistingPoint`는 본문이 비어 있음 | Chapter 3 |
| `ImmersiveCoordinator.swift` | 속성, `init`, 보조 메서드가 있음. `process(position:at:appModel:)`는 본문이 비어 있음 | Chapter 4 |
| `ImmersiveView.swift` | `import Foundation`만 있음 | Chapter 4 |
| `HandConstellationApp.swift` | 제어창 `WindowGroup`만 있음 | Chapter 4에서 `ImmersiveSpace` 추가 |
| `ControlView.swift` | 화면은 완성본이고 `toggleImmersiveSpace()`만 본문이 비어 있음 | Chapter 4 |

비어 있는 곳에는 `// Chapter 3에서 작성합니다.`처럼 작성할 Chapter를 적어 두었습니다.

## 테스트

`HandConstellationTests/DwellDetectorTests.swift`에 머무르기 판정 테스트 6개가 있습니다. Chapter 3에서 `DwellDetector.update(position:at:)`를 작성한 뒤, 실행 대상을 Apple Vision Pro Simulator로 두고 **Product > Test**(⌘U)를 실행하면 모두 통과합니다. 그 전에는 `update`가 없어서 테스트가 빌드되지 않습니다. 테스트는 Test를 실행할 때만 빌드되므로 앱 빌드(⌘B)와 실행(⌘R)에는 영향이 없습니다.

## Simulator에서 그려 보기

Simulator에는 손 추적이 없습니다. Chapter 4를 마친 뒤 Simulator에서 몰입형 공간을 열면 제어창 오른쪽에 **Simulator 입력 패드**가 나타납니다. 그리기를 켜고 패드를 누른 채 0.8초 멈추면 검지를 멈춘 것처럼 점이 찍힙니다. 이 입력은 `SimulatorInputPad.swift`와 `ImmersiveCoordinator.swift`의 `#if targetEnvironment(simulator)` 안에만 있고, 실제 기기용 빌드에는 들어가지 않습니다.

## 기기에서 실행할 때

프로젝트에는 개발 팀이 지정되어 있지 않습니다. Simulator에서는 그대로 실행되고, Apple Vision Pro에 설치할 때는 HandConstellation target의 **Signing & Capabilities**에서 Team을 고르고 필요하면 Bundle Identifier(`com.example.HandConstellation`)를 내 것으로 바꿉니다. 자세한 순서는 Chapter 5에 있습니다.
