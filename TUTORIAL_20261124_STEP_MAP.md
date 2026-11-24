# 2026-11-24 코드 Step 지도

> 2026-11-25 덧붙임: 이 문서를 쓴 뒤 메인 세션이 Simulator에서 입력 패드를 마우스로 눌러 점과 선이 그려지는 것, Xcode 캔버스의 `#Preview`에 점 4개·선 5개 별자리가 보이는 것, 스타터의 머무르기 테스트 6개가 Xcode에서 통과하는 것을 확인했다. 아래에서 "확인하지 못했다"고 적은 항목 가운데 이 세 가지는 확인이 끝났다. 스타터 프로젝트의 `LastUpgradeCheck`는 2710으로 올리고 Xcode 권장 설정을 반영했다.

본문을 다시 쓰는 작업자를 위한 문서다. 앱·스타터·스냅샷을 재구성한 결과를 페이지별 코드 Step, 읽기 전용 Step, 스타터 상태, 화면 문구, 테스트, Simulator 입력 순서로 정리했다. 규칙은 [공통 규칙](TUTORIAL_20261124_EXECUTION_SPEC.md)을 따른다.

스냅샷은 모두 `Scripts/generate_snapshots.py`가 앱 소스에서 만든다. 손으로 고치지 않는다.

## 1. 이름 규칙과 쓰는 법

- 작성 Step: `C{Chapter}-{파일}-{번호}.swift`. `-00`은 스타터에 들어 있는 상태, 마지막 번호는 앱 소스와 바이트까지 같다.
- 읽기 전용 Step: `C{Chapter}-{파일}-…-{꼬리표}.swift`(보여 줄 파일)와 `HL-{파일}-{꼬리표}.swift`(강조 기준) 한 쌍. 한 쌍은 한 Step에서만 쓴다.
- 작성 Step은 `@Code(name: "파일.swift", file: C…-NN.swift, previousFile: C…-(NN-1).swift)`로 쓴다. `reset`은 필요 없다. 다른 파일을 보여 주다가 돌아와도 `previousFile`만 맞으면 된다.
- 읽기 전용 Step은 `@Code(name: "파일.swift", file: C…-꼬리표.swift, previousFile: HL-….swift)`로 쓴다.
- 강조되는 줄은 DocC가 `previousFile`과 비교해 정한다. 아래 표의 "강조 줄"은 DocC와 같은 diff로 계산한 실제 값이다.
- 쓰지 않는 스냅샷이 카탈로그에 남으면 `verify_tutorial.py`가 실패한다. 읽기 전용 쌍을 쓰지 않기로 했으면 `generate_snapshots.py`에서 해당 `reading(...)` 항목을 지우고 `./Scripts/verify-snapshots.sh --generate`를 실행한다. `-00`부터 마지막 번호까지의 작성 스냅샷은 모두 `file`이나 `previousFile`로 한 번 이상 참조해야 한다.
- 다른 줄을 강조하거나 다른 시점의 파일을 보여 주고 싶으면 `reading(이름, 상태, 기준 이름, 줄 범위…)`를 추가한다. 줄 범위는 줄 번호가 아니라 줄의 글자로 찾는다. DocC가 다른 줄을 강조하게 되는 범위는 생성기가 거절한다.

## 2. 페이지별 코드 Step

"줄"은 더한 줄/지운 줄이다. 지운 줄은 모두 임시 줄(빈 본문 주석, `default:`, `break`)이다.

### Chapter 1 · ReadingTheStarterCode (읽기만)

| 순서 | file | previousFile | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- |
| 1 | `C01-HandConstellationApp-scenes.swift` | `HL-HandConstellationApp-scenes.swift` | 8–14 | `body`에 장면이 `WindowGroup` 하나뿐이다. 몰입형 공간은 Chapter 4에서 등록한다. |
| 2 | `C01-HandConstellationApp-environment.swift` | `HL-HandConstellationApp-environment.swift` | 6, 11 | `@State`로 만든 `AppModel` 하나를 `.environment`로 넘긴다. 나중에 몰입형 공간도 같은 객체를 받는다. |
| 3 | `C01-AppModel-drawing.swift` | `HL-AppModel-drawing.swift` | 26–29, 65, 69, 118–120, 122–127, 129–131 | 그리기 상태(`DrawingState`), 공간 ID, `setDrawingEnabled`, `toggleDrawing`. 버튼이 바꾸는 값은 이것뿐이고 코디네이터가 이 값을 읽는다. |
| 4 | `C01-ControlView-toggle.swift` | `HL-ControlView-toggle.swift` | 66, 223–225 | 주 버튼이 `toggleImmersiveSpace()`를 부르지만 본문이 비어 있다. 그래서 스타터에서는 버튼을 눌러도 반응이 없다. Chapter 4에서 작성한다. |

`C01-Info-01.plist`(reset: true)는 권한 페이지에서 쓰던 조각이다. 내용은 그대로다.

### Chapter 2 · StartingTheHandTrackingSession

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C02-HandTrackingService-01.swift` | `C02-HandTrackingService-00.swift` | +16 | 1, 3–17 | `import ARKit`·`simd`와 오류 타입 `HandTrackingServiceError`. 미지원과 권한 거부를 구분해 두어야 코디네이터가 서로 다른 상태로 바꿀 수 있다. |
| 2 | `C02-HandTrackingService-02.swift` | `…-01.swift` | +13 | 19–31 | 클래스, `HandTrackingProvider`, `ARKitSession`, `start()`의 `isSupported` 검사. Simulator는 여기서 `unsupported`를 던진다. `provider`가 `private`이 아닌 이유는 코디네이터가 `anchorUpdates`를 읽기 때문이다. |
| 3 | `C02-HandTrackingService-03.swift` | `…-02.swift` | +12 | 29–40 | 권한 조회 → 정해지지 않았으면 한 번 요청 → 허용이 아니면 `authorizationDenied`. 이미 거부한 사용자에게는 창이 다시 뜨지 않는다. |
| 4 | `C02-HandTrackingService-04.swift` | `…-03.swift` | +6 | 41–46 | `session.run([provider])`와 `stop()`. `run`은 데이터 제공을 시작할 뿐이고 손 앵커는 `anchorUpdates`로 온다. |

### Chapter 2 · ConvertingTheFingertipToWorldSpace

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C02-HandTrackingService-05.swift` | `C02-HandTrackingService-04.swift` | +15 | 48–62 | `rightIndexFingerTipPosition(from:)`의 앞부분. 오른손이 아니거나, 추적이 끊겼거나, 골격이 없거나, 검지 끝 관절이 추적되지 않으면 `nil`. 끝의 `// 다음 Step에서 위치를 계산합니다.`와 `return nil`은 다음 Step에서 지운다. |
| 2 | `C02-HandTrackingService-06.swift` | `…-05.swift` | +6 −2 | 60–65 | `originFromAnchorTransform * anchorFromJointTransform`, 네 번째 열에서 위치 꺼내기, 유한한 값인지 검사. 곱하는 순서가 "원점←앵커←관절"이라는 점. |

### Chapter 3 · DetectingTheDwell

읽기 전용(쓰기 전에 둔다).

| file | previousFile | 강조 줄 | 내용 |
| --- | --- | --- | --- |
| `C03-DwellDetector-00-phase.swift` | `HL-DwellDetector-phase.swift` | 6–10, 12–17 | 밖으로 알리는 `Phase`와 `Snapshot` |
| `C03-DwellDetector-00-state.swift` | `HL-DwellDetector-state.swift` | 19–23, 25–28 | 안에서만 쓰는 `State`(연관 값 포함)와 기준값 세 개 |
| `C03-Configuration-dwell.swift` | `HL-Configuration-dwell.swift` | 5–7 | 0.8초, 1.5cm, 3cm |
| `C03-DwellDetectorTests-commit.swift` | `HL-DwellDetectorTests-commit.swift` | 18, 22–26 | 스타터의 테스트 파일. 0.8초에 한 번만 찍히는지 검사하는 테스트. 마지막 Step(테스트 실행) 앞에 둔다. |

작성 Step.

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C03-DwellDetector-01.swift` | `C03-DwellDetector-00.swift` | +23 | 43–65 | `update`의 입력 검사, `switch state`, `.idle`: 첫 위치에서 머무르기를 시작한다. `default:` 세 줄은 `switch`가 모든 경우를 다루게 하는 임시 줄이고 Step 4에서 지운다. |
| 2 | `C03-DwellDetector-02.swift` | `…-01.swift` | +22 | 60–81 | `.dwelling`: 지난 시간으로 진행률을 구하고, 0.8초가 되면 점을 찍고 `.coolingDown`으로 간다. `1e-9`는 0.1초씩 더한 시간이 0.8에 살짝 못 미치는 부동소수점 오차를 넘기기 위한 값이다. 찍는 위치는 지금 위치가 아니라 머무르기를 시작한 `center`다. |
| 3 | `C03-DwellDetector-03.swift` | `…-02.swift` | +10 | 61–70 | `.dwelling` 맨 앞에 1.5cm 검사를 넣는다. 벗어나면 새 위치에서 다시 0초부터 센다. Step 2 상태로는 손이 움직여도 점이 찍힌다는 점을 짚을 수 있다. |
| 4 | `C03-DwellDetector-04.swift` | `…-03.swift` | +17 −3 | 92–108 | `.coolingDown`: 찍은 자리에서 3cm 넘게 떨어져야 다음 머무르기를 시작한다. 같은 자리에서 점이 계속 찍히는 것을 막는다. `default:`를 이 분기로 바꾼다. |

끝에서 테스트를 실행한다. 스타터의 `HandConstellationTests`에 테스트 6개가 있고, Step 4까지 쓰면 모두 통과한다(7장).

### Chapter 3 · RenderingPointsAndLines

읽기 전용(쓰기 전에 둔다).

| file | previousFile | 강조 줄 | 내용 |
| --- | --- | --- | --- |
| `C03-ConstellationRenderer-00-stubs.swift` | `HL-ConstellationRenderer-stubs.swift` | 24, 35, 39, 49–50, 55 | 스타터에서 비어 있는 다섯 곳: `init`, `updateCursor`, `hideCursor`, `makeLine`, `connectExistingPoint` |
| `C03-ConstellationRenderer-00-guidance.swift` | `HL-ConstellationRenderer-guidance.swift` | 16–21, 26, 62–119 | 스타터가 제공하는 기존 점 연결 안내: 속성 다섯 개, `init`의 호출 한 줄, 확장(extension)의 메서드 다섯 개 |
| `C03-Configuration-rendering.swift` | `HL-Configuration-rendering.swift` | 11–13 | 점 6mm, 선 1.5mm, 커서 5mm(반지름) |

작성 Step.

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C03-ConstellationRenderer-01.swift` | `C03-ConstellationRenderer-00.swift` | +15 −1 | 16–22, 31–38 | 점·선 컨테이너와 이름, 점 메시, 선 굵기, 흰색 `UnlitMaterial` 두 개. `init`의 주석 한 줄을 지우고 쓴다. 컨테이너로 나누는 이유는 초기화할 때 통째로 비우기 위해서다. `UnlitMaterial`은 조명의 영향을 받지 않아 어디서나 같은 흰색으로 보인다. 점 메시는 한 번 만들어 모든 점이 함께 쓴다. |
| 2 | `C03-ConstellationRenderer-02.swift` | `…-01.swift` | +10 | 23–26, 43–48 | 커서 엔티티와 재질 두 개(새 점 모드는 불투명도 0.72, 기존 점 연결 모드는 불투명). 처음에는 `isEnabled = false`로 숨긴다. |
| 3 | `C03-ConstellationRenderer-03.swift` | `…-02.swift` | +10 −2 | 59–67, 71 | `updateCursor`와 `hideCursor`의 본문. 크기는 새 점 모드 0.72배→1.42배, 기존 점 연결 모드 1.0배→1.85배. 진행률은 0–1로 자른다. |
| 4 | `C03-ConstellationRenderer-04.swift` | `…-03.swift` | +12 −2 | 81–92 | `makeLine`의 본문. 원기둥은 y축 방향으로 만들어지므로 길이를 높이로 주고, 중점에 놓고, y축을 두 점의 방향으로 돌린다. 길이가 0이면 방향을 정할 수 없어 `nil`. |
| 5 | `C03-ConstellationRenderer-05.swift` | `…-04.swift` | +23 −1 | 95–115, 118–119 | `addLine`, `addPoint`, `connectExistingPoint`의 본문. 새 점은 구 하나와(첫 점이 아니면) 직전 점에서 오는 선 하나다. 기존 점 연결은 선만 더하고 점은 만들지 않는다. |
| 6 | `C03-ConstellationRenderer-06.swift` | `…-05.swift` | +12 | 121–132 | `reset`. 두 컨테이너를 비우고 안내와 커서를 숨긴다. `children`을 배열로 복사해 도는 이유는 도는 중에 컬렉션이 바뀌기 때문이다. |
| 7 | `C03-ConstellationRenderer-07.swift` | `…-06.swift` | +21 | 198–218 | `#Preview`. 점 4개와 선 5개짜리 예시 별자리(6장). 기기 없이 캔버스에서 결과를 본다. |

### Chapter 4 · BuildingTheCoordinatorLifecycle

읽기 전용. 꼬리표 앞의 번호가 보여 주는 시점이다. 그 시점에 맞춰 둔다.

| file | previousFile | 강조 줄 | 두는 곳 | 내용 |
| --- | --- | --- | --- | --- |
| `C04-ImmersiveCoordinator-00-state.swift` | `HL-ImmersiveCoordinator-state.swift` | 9–18, 20–38 | Step 1 앞 | 속성과 `init`. 렌더러, 감지기 둘, 모델을 설정값 하나로 만든다. |
| `C04-ImmersiveCoordinator-00-drawing.swift` | `HL-ImmersiveCoordinator-drawing.swift` | 64–89 | Step 1 앞 또는 Step 4 앞 | `applyDrawingState`와 `cancelDwell`. 그리기를 끄면 지금 별자리를 끝내므로 다음 점은 새 별자리가 된다. Step 4 앞에 두려면 `reading`의 상태를 3으로 바꾼다. |
| `C04-ImmersiveCoordinator-01-simulator.swift` | `HL-ImmersiveCoordinator-simulator.swift` | 49, 289–304 | Step 1 바로 뒤 | `runWithoutHandTracking`. Simulator에서는 입력 패드가 검지를 대신하고, 그 밖에서는 미지원 상태만 알린다. |
| `C04-ImmersiveCoordinator-05-feedback.swift` | `HL-ImmersiveCoordinator-feedback.swift` | 172–191, 193–210 | Step 6 앞 | `keepCompletionVisible`, `keepRejectionVisible`. 손이 그 자리를 떠날 때까지 안내를 유지하고, 그동안은 `true`를 돌려 나머지 처리를 건너뛴다. |
| `C04-ImmersiveCoordinator-05-connection.swift` | `HL-ImmersiveCoordinator-connection.swift` | 212–226, 234–244, 246–259 | Step 6 앞 | `showConnectionProgress`, `rejectConnection`, `commitConnection`의 연결 성공 부분 |
| `C04-Configuration-connection.swift` | `HL-Configuration-connection.swift` | 8–10 | Step 6 앞 | 연결 시작 3cm, 연결 유지 4cm, 점 사이 최소 3cm |

작성 Step.

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C04-ImmersiveCoordinator-01.swift` | `C04-ImmersiveCoordinator-00.swift` | +24 | 11, 39–61 | `handTrackingService` 속성과 `run(appModel:)`: 권한 확인 중 → 시작 → 추적 중, 오류별 상태, 끝날 때 정리. 미지원은 스타터의 `runWithoutHandTracking`에 맡긴다(한 줄). 이 Step에는 아직 반복문이 없어서 시작하자마자 끝난다. |
| 2 | `C04-ImmersiveCoordinator-02.swift` | `…-01.swift` | +18 | 64–81 | `process(anchor:appModel:)`: 그리기 상태 반영 → 꺼져 있으면 취소 → 검지 위치 → `process(position:…)`. 시간은 `systemUptime`을 쓴다. 시계를 바꿔도 뒤로 가지 않는 값이라 지난 시간을 재기에 맞다. |
| 3 | `C04-ImmersiveCoordinator-03.swift` | `…-02.swift` | +10 | 48–57 | `for await … anchorUpdates` 반복문. 오른손만 처리하고, 작업이 취소되면 빠져나온다. 반복문이 스스로 끝났을 때만 상태를 대기로 돌린다. |
| 4 | `C04-ImmersiveCoordinator-04.swift` | `…-03.swift` | +16 | 74–89 | `drawingStateChanged`와 `reset`. 초기화는 감지기·모델·렌더러를 비우고 제어창의 개수와 안내를 맞춘다. 손 추적은 멈추지 않는다. |
| 5 | `C04-ImmersiveCoordinator-05.swift` | `…-04.swift` | +13 | 90–102 | `stop`. 공간이 닫힐 때 세션을 멈추고, 모두 비우고, 그리기를 끄고, 상태를 대기로 돌린다. |
| 6 | `C04-ImmersiveCoordinator-06.swift` | `…-05.swift` | +25 −1 | 127–151 | `process(position:…)` 앞부분: 유지 중인 안내 두 가지 → 기존 점 연결 감지 → 목표에 머무르는 중이면 연결을 처리하고 `return`. 기존 점 연결을 먼저 보는 이유: 기존 점 3cm 안에서는 새 점이 "너무 가깝다"로 거절되므로, 먼저 연결인지 확인해야 한다. 머무르는 동안 `dwellDetector.trackingLost()`로 새 점 머무르기를 취소한다. |
| 7 | `C04-ImmersiveCoordinator-07.swift` | `…-06.swift` | +13 | 152–164 | 뒷부분: 새 점 머무르기 → 커서 → 모델의 `addPoint` → 렌더러. 모델이 받아들인 점만 그린다. 거절은 `pointRejected`가 안내로 바꾼다. |

Step 6·7이 끝나도 `ImmersiveView`가 없어서 앱 화면은 달라지지 않는다. 이 페이지의 확인은 빌드까지다.

### Chapter 4 · ConnectingTheRealityViewAndAppScenes

| Step | file | previousFile | 줄 | 강조 줄 | 내용과 설명할 점 |
| --- | --- | --- | --- | --- | --- |
| 1 | `C04-ImmersiveView-01.swift` | `C04-ImmersiveView-00.swift` | +14 −1 | 1–14 | `RealityView`에 렌더러의 `rootEntity`를 넣는다. 몰입형 공간의 `RealityView`는 ARKit과 원점이 같아서 손에서 구한 좌표를 그대로 쓴다. `import Foundation`을 지우고 쓴다. |
| 2 | `C04-ImmersiveView-02.swift` | `…-01.swift` | +13 | 13–25 | `.task`로 `run`, `onChange` 두 개로 초기화·그리기 전환, `onDisappear`로 `stop`. `.task`는 화면이 사라지면 취소되므로 반복문이 함께 끝난다. |
| 3 | `C04-HandConstellationApp-01.swift` | `C04-HandConstellationApp-00.swift` | +6 | 14–19 | `ImmersiveSpace` 등록과 `.mixed`. 같은 `appModel`을 넘긴다. `Info.plist`의 `UISceneInitialImmersionStyle`(스타터에 있음)과 맞춘 값이다. |
| 4 | `C04-ControlView-01.swift` | `C04-ControlView-00.swift` | +22 −1 | 6, 225–245 | `openImmersiveSpace`를 환경에서 꺼내고, 닫힘 상태에서 공간을 연다. 결과(`opened`, `userCancelled`, `error`)에 따라 상태를 정한다. 여는 동안 `.transitioning`으로 두어 버튼을 두 번 누르지 못하게 한다. |
| 5 | `C04-ControlView-02.swift` | `…-01.swift` | +9 −1 | 7, 243–250 | `dismissImmersiveSpace`로 닫고 제어창을 처음 상태로 돌린다. `.open`의 `break`를 지우고 쓴다. |

Step 4까지만 쓰면 **체험 종료**를 눌러도 공간이 닫히지 않는다. Simulator 확인은 Step 5 뒤에 둔다. `C04-SimulatorInputPad-region.swift`(previousFile `HL-SimulatorInputPad-region.swift`, 강조 10–12, 17–25)는 패드가 가리키는 영역의 위치·크기와 변환 함수를 보여 주는 읽기 전용 쌍이다. Simulator에서 그려 보는 Step 앞에 둘 수 있다.

## 3. 스타터 상태

| 파일 | 스타터 | 작성 |
| --- | --- | --- |
| `AppModel.swift` (141줄) | 완성본 | 없음 |
| `ConstellationConfiguration.swift` (16줄) | 완성본 | 없음 |
| `ConstellationModel.swift` (211줄) | 완성본 | 없음 |
| `ExistingPointConnectionDetector.swift` (142줄) | 완성본 | 없음 |
| `SimulatorInputPad.swift` (104줄) | 완성본. 파일 전체가 `#if targetEnvironment(simulator)` 안에 있다 | 없음 |
| `Info.plist` | 장면 설정만 있음 | Chapter 1: 권한 설명(Info 탭) |
| `HandTrackingService.swift` | `import Foundation` 한 줄 | Chapter 2: 66줄 전체 |
| `DwellDetector.swift` | 71줄: 타입, 기준값, `init`, `trackingLost`·`beginCooldown`·`reset`, `idleSnapshot`, `hasFiniteComponents` | Chapter 3: `update` 69줄 |
| `ConstellationRenderer.swift` | 120줄: `import` 네 줄, `CursorMode`, `rootEntity`, 안내용 속성 5개, `init`(호출 한 줄), 빈 본문 4개(`updateCursor`, `hideCursor`, `makeLine`, `connectExistingPoint`), 안내 확장 | Chapter 3: 104줄 |
| `ImmersiveCoordinator.swift` | 296줄: 속성(`handTrackingService` 제외), `init`, 빈 `process(position:at:appModel:)`, 보조 메서드 확장 | Chapter 4: 119줄 |
| `ImmersiveView.swift` | `import Foundation` 한 줄 | Chapter 4: 27줄 전체 |
| `HandConstellationApp.swift` | `WindowGroup`만 있음 | Chapter 4: `ImmersiveSpace` 6줄 |
| `ControlView.swift` | 화면 전체. `toggleImmersiveSpace()` 본문과 환경 값 두 줄이 없음 | Chapter 4: 30줄 |
| `HandConstellationTests/DwellDetectorTests.swift` | 테스트 6개(읽기만) | 없음 |

학습자가 쓰는 줄은 모두 421줄이다(이전에는 코디네이터만 343줄을 한 번에 붙여 넣었다).

비어 있는 본문에는 `// Chapter 3에서 작성합니다.` 또는 `// Chapter 4에서 작성합니다.`가 있다. 렌더러 `init`에는 `// Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.`가 있다. 빈 본문을 둔 곳은 스타터의 코드가 부르는 메서드뿐이다. 나머지(`addLine`, `addPoint`, `reset`, `run`, `stop` 등)는 메서드 전체를 새로 쓴다.

코디네이터의 보조 메서드(모두 `private`, 확장 안):

| 이름 | 하는 일 | 부르는 곳 |
| --- | --- | --- |
| `connectionTargets` | 지금 별자리의 다른 점들을 감지기 형식으로 바꾼다 | Step 6 |
| `applyDrawingState(appModel:)` | 그리기 전환을 한 번만 반영한다. 끄면 별자리를 끝낸다 | Step 2, 4 |
| `cancelDwell()` | 진행 중인 머무르기를 취소하고 커서·안내를 숨긴다 | Step 2, 5 |
| `keepCompletionVisible(at:appModel:)` | 방금 연결한 점을 떠날 때(4cm)까지 완료 표시를 유지한다 | Step 6 |
| `keepRejectionVisible(at:appModel:)` | 거절된 자리를 떠날 때(3cm)까지 안내를 유지한다 | Step 6 |
| `showConnectionProgress(_:to:appModel:)` | 목표 강조, 미리보기 선, 진행률 | Step 6 |
| `hideConnectionProgress(appModel:)` | 연결 안내를 숨기고 기본 안내로 돌린다 | Step 6 |
| `rejectConnection(to:appModel:)` | 이미 이어진 점을 거절한다 | Step 6 |
| `commitConnection(to:appModel:)` | 모델과 장면에 선을 더하고 개수를 맞춘다 | Step 6 |
| `pointAdded(appModel:)` | 새 점이 생긴 뒤 감지기·개수·안내를 맞춘다 | Step 7 |
| `pointRejected(_:at:appModel:)` | 거절 이유를 안내로 바꾼다(너무 가까움, 최대 개수, 잘못된 위치) | Step 7 |
| `clearHeldFeedback()` | 유지 중인 완료·거절 위치를 잊는다 | Step 4, 5 |
| `syncCounts(appModel:)` | 모델의 개수를 제어창에 옮긴다 | Step 4, 5 |
| `syncDrawingGuidance(appModel:)` | 그리기 상태와 별자리에 맞는 안내 문장을 고른다 | Step 4 |
| `clearPointLimitFailure(appModel:)` | 최대 개수 안내를 지우고 상태를 되돌린다 | Step 4 |
| `runWithoutHandTracking(appModel:)` | 손 추적이 없는 환경 처리. Simulator에서는 입력 패드로 그린다 | Step 1 |

이전 본문에 나오던 `connectCurrentNode`, `trackingLost(appModel:)`는 없어졌다(`commitConnection`, `cancelDwell`).

## 4. 화면 문구

새로 생긴 문구. 모두 Simulator 빌드에서만 나온다.

| 위치 | 문구 |
| --- | --- |
| 상태 표시(오른쪽 위) | `Simulator 입력` (초록색, 기호 `cursorarrow.rays`) |
| 상태 문장 | `Simulator에서는 입력 패드를 누른 채 멈추면 검지를 멈춘 것처럼 동작합니다.` |
| 패드 제목 | `Simulator 입력 패드` |
| 패드 안내(그리기 켜짐) | `누른 채 0.8초 멈추면 그 자리에 점이 찍혀요.` |
| 패드 안내(그리기 꺼짐) | `그리기를 켜면 입력 패드를 쓸 수 있어요.` |

기존 문구는 한 글자도 바뀌지 않았다. 코드 주석으로 들어간 한국어: `// Chapter 3에서 작성합니다.`, `// Chapter 4에서 작성합니다.`, `// Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.`, `// 다음 Step에서 위치를 계산합니다.`, `// 나머지 상태는 다음 Step에서 채웁니다.`, `// 기존 점 연결 안내에 쓰는 엔티티와 재질입니다. 스타터 프로젝트가 제공합니다.`, `// MARK: - 기존 점 연결 안내 (스타터 프로젝트 제공)`, `// MARK: - 보조 메서드 (스타터 프로젝트 제공)`, `// 점 A, B, C, D를 차례로 찍고 D–A, A–C 선을 더합니다.`

## 5. 새 상태 값과 속성

- `AppModel.TrackingStatus.simulated`: Simulator 빌드에만 있는 경우(`#if targetEnvironment(simulator)`). 손 추적이 미지원일 때 코디네이터가 설정한다.
- `AppModel.simulatedFingertip: SIMD3<Float>?`: Simulator 빌드에만 있다. 패드를 누르는 동안의 위치, 떼면 `nil`. 화면이 이 값 때문에 다시 그려지지 않도록 `@ObservationIgnored`다.
- `AppModel.isInputAvailable`: 검지 위치가 들어오고 있는지. 기기에서는 `trackingStatus == .tracking`과 같다. **그리기 켜기** 버튼이 이 값으로 켜진다.
- 초기화(`reset`)는 이제 상태를 무조건 "추적 중"으로 바꾸지 않는다. 최대 점 개수 안내(`failed`)가 떠 있을 때만 원래 상태(기기: 추적 중, Simulator: Simulator 입력)로 되돌린다.
- 렌더러의 `addPoint(at:segment:)`와 `connectExistingPoint(with:)`에서 `lineRadius` 인자가 없어졌다. 선 굵기는 렌더러가 `init`에서 설정값을 받아 둔다. `makeLine`은 제네릭이 아니고 `UnlitMaterial`을 받는다.
- `process(position:at:appModel:)`는 테스트와 Simulator 입력이 부르므로 `private`이 아니다.

## 6. `#Preview`

`ConstellationRenderer.swift` 맨 아래. `RealityView` 안에서 렌더러를 만들고 A(−0.10, 0.08), B(0.08, 0.10), C(0.11, −0.07), D(−0.08, −0.09)(z는 0, 단위 m)를 차례로 찍은 뒤 D–A, A–C 선을 더한다. 점 4개, 선 5개로 Chapter 5 첫 실습의 모양과 같다. `connectExistingPoint`가 완료 표시를 켜므로 마지막에 `hideConnectionGuidance()`로 끈다.

같은 내용을 창에 넣어 Simulator에서 띄워 보면 창 가운데에 가로 20cm쯤 되는 흰 별자리가 또렷하게 보인다. Xcode 캔버스 자체는 열어 보지 못했다(8장 참고).

## 7. 테스트

| 무엇 | 어떻게 | 결과 |
| --- | --- | --- |
| 스타터의 머무르기 테스트 6개 | Chapter 3에서 `update`를 쓴 뒤 실행 대상을 Apple Vision Pro Simulator로 두고 **Product > Test**(⌘U). 명령줄은 `./Scripts/run-simulator-tests.sh --starter` | 6개 통과 |
| 완성 앱의 테스트 30개 | `./Scripts/run-simulator-tests.sh` | 30개 통과(판정·모델 23개와 코디네이터 7개) |
| 판정·모델 테스트 23개(Mac) | `swift test` | 23개 통과 |
| 코드 Step마다 빌드되는지 | `python3 Scripts/verify_snapshot_builds.py` 또는 `./Scripts/verify-snapshots.sh --builds` | 스타터와 29개 Step 상태가 기기용·Simulator용으로 경고 없이 타입 검사를 통과 |

본문에 쓸 때 알아 둘 점:

- 스타터를 받은 직후에는 `update`가 없어서 ⌘U가 "value of type 'DwellDetector' has no member 'update'" 오류로 실패한다. 테스트는 Test를 실행할 때만 빌드되므로 ⌘B와 ⌘R에는 영향이 없다.
- 테스트는 Simulator에서 앱을 띄운 채 실행된다. 처음 실행하면 Simulator가 켜지는 시간이 걸린다.
- 테스트 이름: `testDoesNotCommitBeforeDuration`, `testCommitsExactlyOnceAfterDuration`, `testLeavingStabilityRadiusRestartsDwell`, `testTrackingLossCancelsCandidate`, `testMovingFarEnoughRearmsDetector`, `testExternalCommitStartsInCooldown`.
- 중간 Step에서 실행하면 일부만 통과한다(Mac에서 실행해 확인). Step 1까지: 4개 실패(`testDoesNotCommitBeforeDuration`, `testCommitsExactlyOnceAfterDuration`, `testMovingFarEnoughRearmsDetector`, `testExternalCommitStartsInCooldown`). Step 2까지: 3개 실패(`testLeavingStabilityRadiusRestartsDwell`, `testMovingFarEnoughRearmsDetector`, `testExternalCommitStartsInCooldown`). Step 3까지: 2개 실패(`testMovingFarEnoughRearmsDetector`, `testExternalCommitStartsInCooldown`). Step 4에서 6개 모두 통과한다. Step마다 통과하는 테스트가 늘어나는 것을 보여 주고 싶으면 이 순서를 쓸 수 있다.

코디네이터 통합 테스트(`HandConstellationTests/ImmersiveCoordinatorTests.swift`, 완성 프로젝트에만 있음)는 가짜 검지 위치를 60분의 1초 간격으로 넣어 Chapter 5의 순서를 그대로 따라간다: A·B·C·D(4점 3선) → A 근처(4점 4선) → C 근처(4점 5선) → B 근처(이미 이어져 거절, 4점 5선) → 그리기 끄고 켜기 → 점 3개(7점 7선, 별자리 2개) → 첫 점 근처(7점 8선) → 초기화(0·0·0). 제어창의 개수와 렌더러 컨테이너의 엔티티 수를 함께 검사한다. Chapter 5의 개수 설명은 이 테스트와 맞춰 두면 된다.

## 8. Simulator 입력 패드

- Simulator에서 몰입형 공간을 열면 제어창 오른쪽에 붙은 패널(ornament)로 나타난다. 공간이 닫혀 있으면 보이지 않는다. 제어창 자체의 크기와 배치는 기기와 같다.
- 패드는 360×240pt다. 몰입형 공간의 가로 45cm·세로 30cm 직사각형에 대응한다. 직사각형의 중심은 원점에서 왼쪽 42cm, 높이 1.55m, 앞 70cm다. Simulator 화면에서는 제어창 왼쪽, 창과 비슷한 높이에 그려진다. 값은 `SimulatorInputPad.swift`의 `SimulatorInputRegion`에 모여 있다.
- 패드를 누르고 있는 동안 그 위치가 검지 위치가 된다. 떼면 검지를 놓친 것과 같이 처리된다(진행 중인 머무르기 취소, 커서 숨김).
- 그리기가 꺼져 있으면 패드가 흐려지고 입력을 받지 않는다.
- 입력은 코디네이터가 1초에 약 60번 읽어 기기와 같은 `process(position:at:appModel:)`에 넣는다. 머무르기, 기존 점 연결, 모델, 렌더러가 기기와 같은 코드로 실행된다. 건너뛰는 것은 손 추적 서비스뿐이다.
- 누른 채 0.8초 멈추면 점이 찍힌다. 3cm는 패드에서 24pt, 1.5cm는 12pt다. 기존 점에 연결하려면 누른 채 커서를 그 점 위로 옮겨 0.8초 멈춘다.
- 확인한 것: 같은 코드 경로에 위치를 넣어 Simulator에서 공간을 열고 점 4개·선 5개와 기존 점 연결 완료 표시까지 그려지는 화면을 캡처로 확인했다. 패드를 마우스로 직접 누르는 조작은 확인하지 못했다.

## 9. 이전 본문에서 사실과 달라진 것

| 페이지 | 이전 내용 | 지금 |
| --- | --- | --- |
| ReadingTheStarterCode | 주 버튼을 누르면 "확인 필요 · Immersive Space를 열 수 없습니다" | 버튼을 눌러도 반응이 없다. 상태는 대기, 그리기 꺼짐, 0·0·0 그대로다 |
| ReadingTheStarterCode, 시작 글 | 스타터 파일 목록 | `SimulatorInputPad.swift`와 `HandConstellationTests/DwellDetectorTests.swift`가 늘었다. `import Foundation`만 있는 파일은 `HandTrackingService.swift`와 `ImmersiveView.swift` 둘뿐이다. `starter-project-files` 그림도 달라져야 한다 |
| ReadingTheStarterCode | `ControlView`는 완성본 | `toggleImmersiveSpace()` 본문이 비어 있다 |
| StartingTheHandTrackingSession | Step 6개(2줄짜리 포함) | 4개. `start()`의 지원 검사는 클래스와 같은 Step이다 |
| ConvertingTheFingertipToWorldSpace | Step 4개, 마지막에 `return` 한 줄 교체 | 2개. 파일 끝의 빈 줄 하나가 없어졌다 |
| DetectingTheDwell | `.dwelling`을 "반경 검사 → 진행률" 순서로 쓰고 임시 `return`을 둠 | "진행률과 찍기 → 반경 검사" 순서. 임시 줄은 `default:` 하나뿐이다. 빌드 결과 Step 대신 테스트 실행 |
| RenderingPointsAndLines | `import Foundation`만 있는 파일에서 시작 | 안내 부분과 빈 본문이 있는 파일에서 시작 |
| RenderingPointsAndLines | 색 있는 `SimpleMaterial`로 쓰고 마지막에 흰색으로 교체 | 처음부터 흰색 `UnlitMaterial` |
| RenderingPointsAndLines | 커서가 0.75배에서 1.5배 | 새 점 모드 0.72배→1.42배, 기존 점 연결 모드 1.0배→1.85배 |
| RenderingPointsAndLines | 안내 구·미리보기 선을 직접 작성 | 스타터 제공. `rootEntity`의 자식 순서는 선, 점, 커서, 안내 |
| RenderingPointsAndLines | `addPoint(at:segment:lineRadius:)` | `addPoint(at:segment:)` |
| BuildingTheCoordinatorLifecycle | 빈 파일에서 시작, 한 Step에 234줄 | 속성·`init`·보조 메서드가 있는 파일에서 시작, Step 7개(10–25줄) |
| BuildingTheCoordinatorLifecycle | 임시 메서드(`Temporary hooks`)를 썼다 지움 | 임시 메서드 없음 |
| ConnectingTheRealityViewAndAppScenes | `ControlView`의 `openImmersiveSpace` 부분을 읽기만 함 | 직접 작성(Step 4·5) |
| ConnectingTheRealityViewAndAppScenes | Simulator에서 공간을 열면 "확인 필요"와 "이 실행 환경에서는 ARKit 손 추적을 사용할 수 없습니다." | "Simulator 입력"(초록)과 4장의 상태 문장. **그리기 켜기**를 누를 수 있고 입력 패드로 점과 선을 그릴 수 있다 |
| 손 추적·좌표 페이지의 퀴즈와 설명 | Simulator에서는 미지원 안내가 뜬다 | `isSupported`가 `false`인 것은 같다. 다만 화면에는 미지원 안내 대신 Simulator 입력이 나온다. "확인 필요 · …사용할 수 없습니다"는 손 추적이 없는 실제 실행 환경에서만 나온다 |
| Chapter 5 | 기기에서만 그릴 수 있다 | 같은 순서를 Simulator에서 입력 패드로 미리 따라 할 수 있다. 권한 창과 손이 보이는 것은 기기에서만 다르다 |
| README(저장소), 검증 문구 | 테스트 23개 | `swift test`는 23개 그대로, Simulator 테스트는 30개 |

## 10. 다시 만들기

```shell
./Scripts/verify-snapshots.sh --generate          # 스냅샷·스타터·zip을 다시 만들고 검사
./Scripts/verify-snapshots.sh --builds            # 검사만 하고, Step마다 타입 검사도 실행
python3 Scripts/generate_snapshots.py --report    # 이 문서의 표에 쓴 줄 수와 강조 줄
python3 Scripts/build_starter_project.py --export 폴더 --chapter 3   # Chapter 3 끝 상태의 프로젝트
```

본문을 고치는 동안에는 `verify_tutorial.py`가 "missing catalog resource"와 "unreferenced catalog assets"를 낸다. 새 `@Code` 참조를 모두 넣으면 사라진다. 퀴즈 검사(보기 2–3개, 정답 하나, 보기마다 `@Justification`)도 같은 스크립트에 들어 있다.
