# 실행과 문제 해결

빌드 환경, 권한, 추적 상태, 머무르기 감도를 차례로 확인합니다.

## 필요한 환경

- visionOS SDK가 들어 있는 최신 안정 버전 Xcode(스타터 프로젝트는 Xcode 16 이상에서 열립니다)
- visionOS 2.0 이상을 실행하는 Apple Vision Pro
- Xcode Settings > Components에 설치된 visionOS 플랫폼과 Simulator runtime
- 손 추적 사용 목적(`NSHandsTrackingUsageDescription`)이 들어간 `Info.plist`

실제 손 관절 입력은 Vision Pro에서만 확인할 수 있습니다. Simulator에서는 제어창, 몰입형 공간 열기와 닫기, 손 추적 미지원 안내까지 볼 수 있고, 검지로 점을 찍는 실습은 할 수 없습니다.

## 지금 단계에서 화면이 달라지지 않음

- Chapter 1에서는 스타터 프로젝트를 실행해 제어창(**대기**, **그리기 꺼짐**, 개수 0)을 확인합니다. **별자리 그리기 시작**을 눌러도 아직 공간이 열리지 않습니다.
- Chapter 2와 3에서는 손 추적 서비스, 머무르기 감지기, 렌더러를 작성하고 빌드로 확인합니다. 아직 아무도 이 코드를 부르지 않으므로 커서나 점이 보이지 않습니다.
- Chapter 4에서 전체를 연결합니다. Simulator에서 공간을 열면 '이 실행 환경에서는 ARKit 손 추적을 사용할 수 없습니다.'가 보이는 것이 맞습니다.
- Chapter 5에서 Vision Pro로 권한 허용 → 커서 → 첫 점 → 다음 점과 선 → 기존 점 연결 순서로 확인합니다.

어느 단계부터 결과가 달라지는지 찾을 때는 각 단계에 적힌 결과와 비교해 보세요. **추적 중**은 세션이 시작됐다는 뜻일 뿐이므로, 검지를 실제로 따라가는지는 그리기를 켠 뒤 커서가 움직이는지로 확인합니다.

## 몰입형 공간이 열리지 않음

1. Chapter 4까지 마쳤는지 확인합니다. 스타터 상태에서는 `ImmersiveSpace` 씬이 아직 없습니다.
2. 제어창에 '확인이 필요합니다: Immersive Space를 열 수 없습니다.'가 보이면 `openImmersiveSpace`가 실패한 것입니다.
3. `ImmersiveSpace` 선언과 `ControlView`의 호출이 같은 `AppModel.immersiveSpaceID`를 쓰는지 확인합니다.
4. 다른 몰입형 공간이 이미 열려 있다면 닫고 다시 시도합니다.

## 손 추적 권한이 거부됨

앱의 최종 Info.plist에 `NSHandsTrackingUsageDescription`이 들어 있는지 확인합니다. 이미 거부했다면 기기의 설정에서 앱의 손 추적 권한을 바꾼 뒤 다시 실행합니다.

제어창의 상태 표시는 다음과 같습니다.

- 대기: 공간을 열기 전이거나 추적이 끝난 상태
- 권한 확인 중: 손 추적 권한을 확인하고 세션을 시작하는 중
- 추적 중: 손 추적 세션이 실행 중
- 확인 필요: 권한 거부, 실행 환경 미지원, 실행 오류 중 하나. 아래에 함께 나오는 안내 문장을 보면 어느 쪽인지 알 수 있습니다.

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

## 점이 너무 쉽게 또는 너무 어렵게 생김

`ConstellationConfiguration.standard`의 값을 조절합니다.

- 움직이는 중에도 점이 생기면 `dwellDuration`을 늘리거나 `stabilityRadius`를 줄입니다.
- 손 떨림 때문에 점이 생기지 않으면 `stabilityRadius`를 조금 늘립니다.
- 같은 자리에 점이 반복해서 생기면 `rearmDistance`와 `minimumPointDistance`를 늘립니다.
- 다음 점을 찍으려고 너무 멀리 움직여야 하면 `rearmDistance`를 줄입니다.

한 번에 한 값만 바꾸고, 실제로 팔을 뻗는 거리에서 여러 번 확인하는 것이 좋습니다.

## 선의 방향이나 길이가 이상함

RealityKit의 원기둥 메시는 로컬 Y축 방향으로 놓입니다. 그래서 두 점의 중점에 원기둥을 두고, `[0, 1, 0]`을 두 점 사이 방향으로 돌리는 회전을 적용해야 합니다. 두 점 사이 거리가 0에 가까우면 선을 만들지 않습니다. 자세한 내용은 Chapter 3의 <doc:RenderingPointsAndLines>를 참고하세요.

## 기존 점에 연결한 뒤 다음 입력이 시작되지 않음

연결이 끝나면 완료 표시가 남고, 연결한 점에서 4cm 이상 멀어져야 사라집니다. 완료 표시가 사라졌는지 먼저 확인한 뒤 다음 목표로 이동하세요. 새 점을 찍은 뒤 3cm 움직여야 하는 조건과는 다른 조건입니다.

## 로컬에서 빌드하기

앱 target을 명령줄에서 빌드합니다. 스타터 프로젝트 폴더에서도 같은 명령을 쓸 수 있습니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

이 저장소의 완성본에는 ARKit에 의존하지 않는 로직의 단위 테스트가 들어 있습니다. 스타터 프로젝트에는 `Package.swift`와 테스트가 없으므로 이 명령은 저장소 루트에서만 실행됩니다.

```shell
swift test
```

`generic/platform=visionOS` destination을 찾을 수 없다는 메시지가 나오면 Xcode Settings > Components에서 visionOS 플랫폼을 설치하세요.
