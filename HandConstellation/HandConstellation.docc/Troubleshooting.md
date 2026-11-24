# 실행과 문제 해결

빌드 환경, 단계별 결과, 권한, 추적 상태, 머무르기 감도를 차례로 확인합니다.

## 필요한 환경

- visionOS SDK가 들어 있는 Xcode(스타터 프로젝트는 Xcode 16 이상에서 열립니다)
- Xcode Settings > Components에 설치된 visionOS 플랫폼과 Simulator runtime
- 실제 손으로 그리려면 visionOS 2.0 이상을 실행하는 Apple Vision Pro

기기가 없어도 Chapter 5까지 따라갈 수 있습니다. Simulator에는 손 추적이 없지만, 몰입형 공간을 열면 제어창 오른쪽에 나타나는 입력 패드가 검지를 대신합니다. 권한 창, 내 손이 보이는 화면, 실제 손 떨림에 대한 감도는 Vision Pro에서만 확인할 수 있습니다.

## 단계마다 보이는 결과

- Chapter 1: 스타터를 Simulator에서 실행하면 제어창이 **대기**, **그리기 꺼짐**, **별자리 0개 · 점 0개 · 선 0개**로 뜹니다. **별자리 그리기 시작**을 눌러도 아직 반응이 없습니다. 버튼이 부르는 `toggleImmersiveSpace()`의 본문은 Chapter 4에서 작성합니다.
- Chapter 2: 손 추적 서비스를 작성하고 빌드로 확인합니다. 아직 아무도 이 코드를 부르지 않으므로 화면은 그대로입니다.
- Chapter 3: 머무르기 판정을 작성한 뒤 **Product > Test**로 스타터의 테스트 6개가 통과하는지 보고, 렌더러를 작성한 뒤 Xcode 캔버스의 `#Preview`에서 점 4개와 선 5개를 봅니다.
- Chapter 4: 코디네이터를 작성하는 동안은 빌드로만 확인합니다. 몰입형 공간과 제어창 버튼까지 연결하면 Simulator에서 공간이 열리고, 상태가 **Simulator 입력**으로 바뀌며, 입력 패드로 점과 선을 그릴 수 있습니다.
- Chapter 5: Vision Pro에서 권한을 허용한 뒤 커서 → 첫 점 → 다음 점과 선 → 기존 점 연결 → 두 번째 별자리 순서로 확인합니다. 그리기 실습은 Simulator 입력 패드로도 같은 순서를 따라 할 수 있습니다.

어느 단계부터 결과가 달라지는지 찾을 때는 각 단계에 적힌 결과와 비교해 보세요. **추적 중**은 세션이 시작됐다는 뜻일 뿐이므로, 검지를 실제로 따라가는지는 그리기를 켠 뒤 커서가 움직이는지로 확인합니다.

## 머무르기 테스트가 실패함

- 스타터를 받은 직후에는 `update`가 없어서 "value of type 'DwellDetector' has no member 'update'" 오류로 테스트가 빌드되지 않습니다. Chapter 3에서 `update(position:at:)`를 작성한 뒤 실행하세요.
- `update`를 중간까지만 썼다면 일부 테스트만 통과합니다. 1.5cm 검사를 넣기 전에는 `testLeavingStabilityRadiusRestartsDwell`이, `.coolingDown` 분기를 쓰기 전에는 `testMovingFarEnoughRearmsDetector`와 `testExternalCommitStartsInCooldown`이 실패합니다.
- 실행 대상이 Apple Vision Pro Simulator인지 확인합니다. 처음 실행하면 Simulator가 켜지는 데 시간이 걸립니다.

## 몰입형 공간이 열리지 않음

1. Chapter 4까지 마쳤는지 확인합니다. 스타터 상태에서는 `ImmersiveSpace` 장면이 없고, `toggleImmersiveSpace()`의 본문도 비어 있습니다.
2. 제어창에 '확인이 필요합니다: Immersive Space를 열 수 없습니다.'가 보이면 `openImmersiveSpace`가 실패한 것입니다. `ImmersiveSpace` 선언과 `ControlView`의 호출이 같은 `AppModel.immersiveSpaceID`를 쓰는지 확인합니다.
3. **체험 종료**를 눌러도 공간이 닫히지 않으면 `toggleImmersiveSpace()`의 `.open` 분기에서 `dismissImmersiveSpace()`를 부르는지 확인합니다.
4. 다른 앱의 몰입형 공간이 이미 열려 있다면 닫고 다시 시도합니다.

## 손 추적 권한이 거부됨

권한 창에는 Chapter 1에서 Info 탭에 추가한 사용 목적 문장(`NSHandsTrackingUsageDescription`)이 나옵니다. 이 항목이 없으면 앱이 손 추적 권한을 받을 수 없습니다. 권한 창이 뜨지 않거나 앱이 바로 종료되면 이 항목을 확인하세요. Info 탭에서 추가한 문장은 `Info.plist` 파일이 아니라 빌드 설정 `INFOPLIST_KEY_NSHandsTrackingUsageDescription`에 저장됩니다.

이미 거부했다면 권한 창이 다시 뜨지 않습니다. 기기의 설정에서 앱의 손 추적 권한을 바꾼 뒤 공간을 다시 여세요.

제어창의 상태 표시는 다음과 같습니다.

- 대기: 공간을 열기 전이거나 추적이 끝난 상태
- 권한 확인 중: 손 추적 권한을 확인하고 세션을 시작하는 중
- 추적 중: 기기에서 손 추적 세션이 실행 중
- Simulator 입력: Simulator에서 입력 패드가 검지를 대신하는 중(Simulator 빌드에만 있음)
- 확인 필요: 권한 거부, 실행 환경 미지원, 실행 오류, 최대 점 개수 도달 중 하나. 아래에 함께 나오는 안내 문장을 보면 어느 쪽인지 알 수 있습니다.

## 커서가 보이지 않음

먼저 제어창이 **그리기 켜짐**인지 확인합니다. 공간은 원하지 않는 점이 생기지 않도록 그리기가 꺼진 상태로 열리므로 **그리기 켜기** 버튼을 눌러야 합니다.

앱은 오른손만 처리하므로 오른손 검지를 씁니다. 그리기가 켜진 뒤 아래 조건이 모두 맞아야 위치가 만들어집니다.

```swift
anchor.chirality == .right
anchor.isTracked
anchor.handSkeleton != nil
indexFingerTip.isTracked
```

손 전체가 시야에 들어오게 하고, 조명이나 손이 가려진 정도를 바꿔 보세요. 관절 추적이 끊기면 앱은 커서를 숨기고 진행 중인 머무르기를 취소합니다.

## Simulator에서 그려지지 않음

- 입력 패드는 Simulator에서 몰입형 공간을 열었을 때만 제어창 오른쪽에 나타납니다. 기기용 빌드에는 없습니다.
- 패드가 흐리고 '그리기를 켜면 입력 패드를 쓸 수 있어요.'가 보이면 **그리기 켜기**를 누르세요.
- 패드는 누르고 있는 동안만 검지 위치가 됩니다. 누른 채 0.8초 멈춰야 점이 찍히고, 손을 떼면 진행 중인 머무르기가 취소됩니다.
- 점과 선은 제어창 왼쪽 공간에 그려집니다. 패드에서 24pt가 3cm이므로 점 사이를 그보다 넉넉히 띄우세요.
- 패드를 뗐다가 마지막 점 가까이를 다시 누르면 '기존 점과 너무 가까워요. 조금 더 이동한 뒤 머물러 주세요.'가 나옵니다. 더 떨어진 곳을 누르세요.

## 점이 너무 쉽게 또는 너무 어렵게 생김

`ConstellationConfiguration.standard`의 값을 조절합니다.

- 움직이는 중에도 점이 생기면 `dwellDuration`을 늘리거나 `stabilityRadius`를 줄입니다.
- 손 떨림 때문에 점이 생기지 않으면 `stabilityRadius`를 조금 늘립니다.
- 같은 자리에 점이 반복해서 생기면 `rearmDistance`와 `minimumPointDistance`를 늘립니다.
- 다음 점을 찍으려고 너무 멀리 움직여야 하면 `rearmDistance`를 줄입니다.

한 번에 한 값만 바꾸고, 실제로 팔을 뻗는 거리에서 여러 번 확인하세요.

## 선의 방향이나 길이가 이상함

RealityKit의 원기둥 메시는 로컬 y축 방향으로 만들어집니다. 그래서 두 점의 중점에 원기둥을 두고, `[0, 1, 0]`을 두 점 사이 방향으로 돌리는 회전을 적용합니다. 두 점 사이 거리가 0이면 방향을 정할 수 없어 선을 만들지 않습니다. 자세한 내용은 Chapter 3의 <doc:RenderingPointsAndLines>를 참고하세요.

## 기존 점에 연결되지 않거나 점이 늘어남

- 기존 점 위에서 머물렀는데 새 점이 생기면 `process(position:at:appModel:)`가 기존 점 연결을 새 점 머무르기보다 먼저 확인하는지 봅니다.
- 연결 판정은 지금 그리는 별자리의 점만 대상으로 합니다. 그리기를 껐다 켠 뒤에는 앞 별자리의 점에 연결되지 않고, 그 근처에 새 점이 생깁니다.
- 연결이 끝나면 완료 표시가 남고, 연결한 점에서 4cm 이상 멀어져야 사라집니다. 완료 표시가 사라진 뒤 다음 목표로 이동하세요. 새 점을 찍은 뒤 3cm 움직여야 하는 조건과는 다른 조건입니다.

## 초기화나 그리기 끄기가 이상하게 동작함

- **그리기 끄기**를 누르는 순간 별자리가 사라지면 `ImmersiveView`의 두 `.onChange`가 부르는 메서드가 서로 바뀌지 않았는지 확인합니다.
- **초기화** 뒤 개수는 0인데 점과 선이 남아 있으면 `.onChange(of: appModel.resetGeneration)`이 `coordinator.reset(appModel:)`을 부르는지 확인합니다.
- 초기화는 그리기 상태를 바꾸지 않습니다. 그리기가 켜진 채로 한곳에 머물면 곧바로 새 점이 생깁니다.

## 로컬에서 빌드하고 테스트하기

앱 타깃을 명령줄에서 빌드합니다. 스타터 프로젝트 폴더에서도 같은 명령을 쓸 수 있습니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

저장소 루트에서는 ARKit과 RealityKit이 필요 없는 로직의 단위 테스트를 Mac에서 실행할 수 있습니다. 스타터 프로젝트에는 `Package.swift`가 없으므로 이 명령은 저장소 루트에서만 동작합니다.

```shell
swift test
```

visionOS Simulator에서 실행하는 테스트는 스크립트로 실행합니다. 옵션 없이 실행하면 완성 앱의 테스트(코디네이터 통합 테스트 포함)를, `--starter`를 붙이면 Chapter 3 끝 상태의 스타터에서 머무르기 테스트를 실행합니다. 다른 Simulator를 쓰려면 `DESTINATION` 환경 변수로 지정합니다.

```shell
./Scripts/run-simulator-tests.sh
./Scripts/run-simulator-tests.sh --starter
```

`generic/platform=visionOS` destination을 찾을 수 없다는 메시지가 나오면 Xcode Settings > Components에서 visionOS 플랫폼을 설치하세요.
