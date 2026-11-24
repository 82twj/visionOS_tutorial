# 앱 구조 이해하기

손 추적 데이터가 RealityKit 엔티티가 되기까지 어떤 타입을 거치는지 살펴봅니다.

## Overview

Hand Constellation은 매 프레임 바뀌는 입력과 오래 남는 별자리 데이터를 서로 다른 타입에 나눠 둡니다. 덕분에 추적이 잠시 끊겨도 저장된 점과 선은 그대로 남고, 머무르기 판정과 점 연결 규칙은 ARKit이나 RealityKit 없이 테스트할 수 있습니다.

검지 위치는 기기에서는 손 추적에서, Simulator에서는 입력 패드에서 옵니다. 두 경로 모두 코디네이터의 `process(position:at:appModel:)`로 들어가므로, 그 뒤의 판정과 그리기는 같은 코드로 실행됩니다.

```text
HandTrackingProvider            SimulatorInputPad (Simulator 빌드에만 있음)
   │ HandAnchor                    │ AppModel.simulatedFingertip
   ▼                               │
HandTrackingService                │
   │ 검지 끝 월드 좌표               │
   ▼                               ▼
ImmersiveCoordinator.process(position:at:appModel:)
   ├── ExistingPointConnectionDetector ── 기존 점에 연결할지 판정
   ├── DwellDetector ── 새 점을 찍을 위치
   ├── ConstellationModel ── 별자리별 점과 선, 다음 선의 시작점
   └── ConstellationRenderer ── 흰색 점·선·커서·연결 안내
```

## 파일과 작성 위치

튜토리얼은 스타터 프로젝트에서 시작합니다. 공간 컴퓨팅과 직접 관련된 코드만 직접 작성하고, 나머지는 스타터에 완성된 채로 들어 있습니다. 빈 본문에는 `// Chapter 3에서 작성합니다.`처럼 작성할 Chapter가 적혀 있습니다.

| 파일 | 스타터 상태 | 작성하는 곳 |
| --- | --- | --- |
| `AppModel`, `ConstellationConfiguration`, `ConstellationModel`, `ExistingPointConnectionDetector`, `SimulatorInputPad` | 완성본 | 고치지 않고 그대로 씁니다 |
| `Info.plist` | 장면 설정만 있음 | Chapter 1: Info 탭에서 손 추적 사용 목적 추가 |
| `HandTrackingService` | `import Foundation`만 있음 | Chapter 2: 파일 전체 |
| `DwellDetector` | 상태 타입, 기준값, `init`, 보조 메서드 | Chapter 3: `update(position:at:)` |
| `ConstellationRenderer` | `CursorMode`, `rootEntity`, 기존 점 연결 안내, 빈 본문 네 곳 | Chapter 3: 점·선·커서, `reset()`, `#Preview` |
| `ImmersiveCoordinator` | 속성, `init`, 빈 `process(position:at:appModel:)`, 보조 메서드 | Chapter 4: `handTrackingService` 속성, `run(appModel:)`, `process(anchor:appModel:)`, `drawingStateChanged(appModel:)`, `reset(appModel:)`, `stop(appModel:)`, `process(position:at:appModel:)`의 본문 |
| `ImmersiveView` | `import Foundation`만 있음 | Chapter 4: 파일 전체 |
| `HandConstellationApp` | `WindowGroup`만 있음 | Chapter 4: `ImmersiveSpace` 추가 |
| `ControlView` | 화면은 완성본, `toggleImmersiveSpace()`의 본문만 비어 있음 | Chapter 4: 공간 열기와 닫기 |
| `HandConstellationTests/DwellDetectorTests` | 테스트 6개 | 고치지 않고 Chapter 3에서 실행합니다 |

## 타입별 역할

### 앱과 장면

`HandConstellationApp`은 제어창용 `WindowGroup`과 손 추적용 `ImmersiveSpace`를 선언합니다. 두 장면은 같은 `AppModel`을 받습니다. `AppModel`에는 공간이 열렸는지, 손 추적 상태, 그리기 켜짐 여부, 별자리·점·선 개수, 안내 문장, 초기화 요청 번호(`resetGeneration`)가 들어 있습니다. **그리기 켜기** 버튼은 공간이 열려 있고 `isInputAvailable`이 참일 때만 눌립니다. 이 값은 기기에서는 상태가 추적 중일 때, Simulator에서는 Simulator 입력일 때도 참입니다.

`ControlView`의 `toggleImmersiveSpace()`는 공간이 닫혀 있으면 `openImmersiveSpace`로 열고, 열려 있으면 `dismissImmersiveSpace`로 닫은 뒤 제어창을 처음 상태로 돌립니다. 여는 동안에는 상태를 `.transitioning`으로 두어 버튼이 두 번 눌리지 않게 합니다.

`ImmersiveView`는 `RealityView`에 렌더러의 루트 엔티티를 한 번 추가하고, `.task`에서 코디네이터의 `run(appModel:)`을 실행합니다. 공간이 닫히면 작업이 취소되면서 추적도 멈춥니다. 그리기 상태와 초기화 요청 번호가 바뀌면 `.onChange`로 코디네이터에 알리고, 화면이 사라지면 `stop(appModel:)`을 부릅니다. 몰입형 공간의 `RealityView`는 ARKit과 같은 원점을 쓰므로, 손 앵커에서 구한 월드 좌표를 엔티티의 `position`에 그대로 넣습니다.

### 손 추적

`HandTrackingService`는 ARKit만 다룹니다. `start()`는 손 추적을 지원하는지 확인하고, 권한이 정해지지 않았을 때만 한 번 요청한 뒤 세션을 실행합니다. 지원하지 않으면 `HandTrackingServiceError.unsupported`를, 권한이 없으면 `.authorizationDenied`를 던집니다. `rightIndexFingerTipPosition(from:)`은 오른손 앵커의 변환과 검지 끝 관절의 변환을 곱해 검지 끝의 월드 좌표를 돌려줍니다.

### ARKit에 의존하지 않는 로직

`DwellDetector`, `ExistingPointConnectionDetector`, `ConstellationModel`은 ARKit도 RealityKit도 가져오지 않습니다. 그래서 머무르기 시간과 반경, 가장 가까운 목표 유지, 중복 선 막기, 별자리 나누기를 Mac에서 단위 테스트로 확인할 수 있습니다.

### 장면 그리기

`ConstellationRenderer`의 루트 엔티티 아래에는 선 컨테이너, 점 컨테이너, 커서, 연결 안내가 차례로 붙어 있습니다. 점과 선은 조명의 영향을 받지 않는 흰색 `UnlitMaterial`로 그립니다. 커서는 머무르는 동안 커지는데, 새 점을 찍을 때는 반투명하게 0.72배에서 1.42배까지, 기존 점에 연결할 때는 불투명하게 1.0배에서 1.85배까지 커집니다. 기존 점 가까이에 가면 그 점을 강조하고 지금 시작점에서 목표까지 미리보기 선을 보여 줍니다. 이 연결 안내 부분은 스타터가 제공합니다. 렌더러는 코디네이터가 넘겨준 값만 그리며 ARKit 세션은 알지 못합니다.

### 코디네이터

`ImmersiveCoordinator`는 손 추적, 두 감지기, 모델, 렌더러를 한곳에서 부릅니다. 튜토리얼에서 작성하는 부분은 수명(`run`, `reset`, `stop`)과 한 프레임의 처리 순서이고, 안내 문구와 개수를 맞추는 보조 메서드는 스타터가 파일 아래쪽의 확장(extension)에 넣어 두었습니다.

| 보조 메서드 | 하는 일 |
| --- | --- |
| `applyDrawingState(appModel:)` | 그리기 전환을 한 번만 반영합니다. 끄면 지금 별자리를 마칩니다 |
| `cancelDwell()` | 진행 중인 머무르기를 취소하고 커서와 연결 안내를 숨깁니다 |
| `keepCompletionVisible(at:appModel:)` | 방금 연결한 점에서 4cm 멀어질 때까지 완료 표시를 유지합니다 |
| `keepRejectionVisible(at:appModel:)` | 거절된 자리에서 3cm 멀어질 때까지 안내를 유지합니다 |
| `showConnectionProgress(_:to:appModel:)`, `hideConnectionProgress(appModel:)` | 목표 강조, 미리보기 선, 진행률을 보이거나 숨깁니다 |
| `rejectConnection(to:appModel:)` | 이미 선으로 이어진 점을 거절합니다 |
| `commitConnection(to:appModel:)` | 모델과 장면에 선을 하나 더하고 개수를 맞춥니다 |
| `pointAdded(appModel:)`, `pointRejected(_:at:appModel:)` | 새 점이 생긴 뒤 개수와 안내를 맞추거나, 거절 이유를 안내로 바꿉니다 |
| `syncCounts(appModel:)`, `syncDrawingGuidance(appModel:)` | 모델의 개수와 알맞은 안내 문장을 제어창에 옮깁니다 |
| `runWithoutHandTracking(appModel:)` | 손 추적이 없는 실행 환경을 처리합니다. Simulator에서는 입력 패드로 그립니다 |

이 밖에 지금 별자리의 다른 점을 감지기 형식으로 바꾸는 `connectionTargets`, 유지 중인 완료·거절 위치를 잊는 `clearHeldFeedback()`, 초기화 뒤 최대 점 개수 안내를 지우는 `clearPointLimitFailure(appModel:)`가 있습니다.

## 한 프레임에서 일어나는 일

1. `run(appModel:)`의 반복문이 `anchorUpdates`에서 오른손 앵커만 골라 `process(anchor:appModel:)`에 넘깁니다.
2. 제어창의 그리기 상태를 먼저 반영합니다. 그리기가 꺼져 있으면 진행 중인 머무르기를 취소하고 멈춥니다.
3. 서비스가 검지 끝을 월드 좌표로 바꿉니다. 좌표를 얻지 못하면 진행 중인 머무르기만 취소합니다.
4. `process(position:at:appModel:)`는 방금 연결한 점에서 4cm, 거절된 자리에서 3cm 안에 있는 동안 완료 표시나 거절 안내만 유지하고 나머지를 건너뜁니다.
5. 기존 점 연결 감지기가 지금 별자리의 점 가운데 목표를 찾습니다. 목표에 머무르는 동안에는 새 점 머무르기를 취소합니다. 이미 이어진 점이면 바로 거절 안내를 보여 주고, 아니면 0.8초가 찰 때 새 점 없이 선만 하나 더한 뒤 목표 점을 다음 선의 시작점으로 삼습니다.
6. 목표가 없으면 머무르기 감지기가 새 점 위치를 한 번만 내보내고, 커서가 진행률에 따라 커집니다.
7. 모델이 새 점을 받으면 렌더러가 점과(시작점이 있으면) 선을 그리고 제어창의 개수와 안내를 맞춥니다. 같은 별자리의 점과 3cm보다 가까운 점은 모델이 받지 않고, 제어창에 이유를 안내합니다.

기존 점 연결을 새 점보다 먼저 확인하는 이유는 기존 점 3cm 안에서는 새 점이 "너무 가깝다"로 거절되기 때문입니다. 추적이 끊기면 두 감지기의 진행 상태를 취소하고 커서와 연결 안내를 숨깁니다. 이미 만든 별자리는 **초기화**를 누르거나 몰입형 공간을 닫을 때까지 남아 있습니다. 초기화는 손 추적을 멈추지 않고, 공간을 닫을 때 부르는 `stop(appModel:)`은 세션을 멈춘 뒤 모두 비우고 그리기를 끕니다.

## Simulator에서 일어나는 일

Simulator에는 손 추적이 없어서 `start()`가 `.unsupported`를 던집니다. `run(appModel:)`은 이 오류를 `runWithoutHandTracking(appModel:)`에 넘기고, Simulator 빌드에서 이 메서드는 상태를 `.simulated`(제어창의 **Simulator 입력**)로 바꾼 뒤 공간이 닫힐 때까지 약 16ms마다 `AppModel.simulatedFingertip`을 읽어 `process(position:at:appModel:)`에 넣습니다. 위 4–7단계는 기기와 똑같이 실행되고, 손 추적 서비스만 건너뜁니다.

입력 패드는 Simulator에서 공간을 열면 제어창 오른쪽에 붙어 나타납니다. 크기는 360×240pt이고, 몰입형 공간의 가로 45cm·세로 30cm 직사각형에 대응합니다. 직사각형의 중심은 원점에서 왼쪽 42cm, 높이 1.55m, 앞 70cm이므로 점과 선은 제어창 왼쪽에 그려집니다. 패드에서 24pt가 3cm, 12pt가 1.5cm입니다. 패드를 누르고 있는 동안 그 위치가 검지 위치가 되고, 떼면 검지를 놓친 것처럼 진행 중인 머무르기가 취소됩니다. 그리기가 꺼져 있으면 패드가 흐려지고 입력을 받지 않습니다. 위치와 크기는 `SimulatorInputPad.swift`의 `SimulatorInputRegion`에서 바꿀 수 있습니다.

`SimulatorInputPad.swift` 전체와 코디네이터의 Simulator 처리, `TrackingStatus.simulated`, `simulatedFingertip`은 모두 `#if targetEnvironment(simulator)` 안에 있습니다. 기기용 빌드에는 들어가지 않고, Simulator가 아닌 실행 환경에서 손 추적을 지원하지 않으면 제어창에 **확인 필요**와 '이 실행 환경에서는 ARKit 손 추적을 사용할 수 없습니다.'만 표시합니다.

## 설정값

체험의 감도와 크기는 `ConstellationConfiguration.standard` 한 곳에서 조절합니다.

| 설정 | 기본값 | 쓰임 |
| --- | ---: | --- |
| `dwellDuration` | 0.8초 | 점을 찍거나 기존 점에 연결하기까지 머무르는 시간 |
| `stabilityRadius` | 0.015m | 같은 자리에 머무른다고 보는 흔들림 반경 |
| `rearmDistance` | 0.03m | 점을 찍은 뒤 다음 머무르기를 시작하려면 움직여야 하는 거리 |
| `connectionSnapDistance` | 0.03m | 기존 점을 연결 목표로 고르는 거리 |
| `connectionReleaseDistance` | 0.04m | 고른 목표를 놓아주는 거리 |
| `minimumPointDistance` | 0.03m | 모델이 너무 가까운 새 점을 받지 않는 거리 |
| `pointRadius` | 0.006m | 점의 반지름 |
| `lineRadius` | 0.0015m | 선의 반지름 |
| `cursorRadius` | 0.005m | 커서의 반지름 |
| `maximumPointCount` | 100 | 한 장면에 둘 수 있는 점의 최대 개수 |

실제 기기에서 손 떨림과 팔을 뻗는 거리를 관찰한 뒤 `stabilityRadius`와 `dwellDuration`을 함께 조절해 보세요.

## 테스트

| 파일 | 확인하는 것 | 실행 |
| --- | --- | --- |
| `DwellDetectorTests` | 0.8초에 한 번만 찍기, 1.5cm를 벗어나면 다시 세기, 추적이 끊기면 취소, 3cm 움직이면 다음 머무르기 | 스타터에도 있습니다. Simulator에서 **Product > Test**, 또는 저장소에서 `swift test` |
| `ExistingPointConnectionDetectorTests` | 시작점에서 먼저 벗어나기, 가장 가까운 목표 고르고 유지하기, 4cm 밖에서 놓기 | `swift test` |
| `ConstellationModelTests` | 점과 선 추가, 기존 점 연결, 중복 선 거절, 별자리 나누기, 초기화 | `swift test` |
| `ImmersiveCoordinatorTests` | 가짜 검지 위치로 Chapter 5의 순서를 재현하고 제어창 개수와 렌더러의 엔티티 수 비교 | `./Scripts/run-simulator-tests.sh` |

`swift test`는 RealityKit이 필요 없는 테스트 23개를 Mac에서 실행합니다. `./Scripts/run-simulator-tests.sh`는 visionOS Simulator에서 코디네이터 테스트까지 30개를 실행하고, `--starter`를 붙이면 Chapter 3 끝 상태의 스타터에서 머무르기 테스트 6개를 실행합니다.
