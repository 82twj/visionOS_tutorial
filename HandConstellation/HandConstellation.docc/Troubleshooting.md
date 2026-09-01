# 실행과 문제 해결

빌드 환경, 권한, 추적 상태, 체류 감도를 순서대로 확인합니다.

## 필수 환경

- visionOS SDK를 포함한 최신 안정 버전 Xcode
- visionOS 2.0 이상을 실행하는 Apple Vision Pro
- Xcode Settings > Components에 설치된 visionOS 플랫폼과 필요한 Simulator runtime
- 손 추적 사용 설명이 포함된 `Info.plist`

ARKit 관절 데이터는 실제 기기에서 확인하는 것이 가장 확실합니다. Simulator에서는 앱의 창과 문서 빌드는 확인할 수 있지만 실제 손의 추적 품질과 권한 흐름을 완전히 대신하지 못합니다.

## 몰입형 공간이 열리지 않음

1. 앱의 Start 버튼을 눌렀을 때 `openImmersiveSpace` 결과를 확인합니다.
2. 동일한 ID를 `ImmersiveSpace` 선언과 호출 양쪽에서 사용하는지 확인합니다.
3. 기존 몰입형 공간이 열려 있다면 닫은 뒤 다시 시도합니다.

## 손 추적 권한이 거부됨

`NSHandsTrackingUsageDescription`이 앱의 최종 Info.plist에 포함되어 있는지 확인합니다. 사용자가 이미 권한을 거부했다면 기기의 개인정보 보호 설정에서 앱의 권한을 변경한 뒤 다시 실행합니다.

앱은 권한 상태를 다음처럼 구분합니다.

- 요청 중: 시스템 권한 UI를 기다리는 상태
- 추적 중: provider가 실행 중인 상태
- 거부됨: 사용자가 손 추적을 허용하지 않은 상태
- 미지원: 현재 기기나 실행 환경이 hand tracking을 제공하지 않는 상태

## 커서가 보이지 않음

먼저 제어 창의 상태가 **그리기 켜짐**인지 확인합니다. 공간은 의도하지 않은 점을 막기 위해 그리기 꺼짐 상태로 시작하므로 **그리기 켜기** 버튼을 누르세요.

오른손만 처리하도록 구현되어 있으므로 오른손 검지를 사용합니다. 그리기가 켜진 뒤 다음 조건을 모두 만족해야 위치가 만들어집니다.

```swift
anchor.chirality == .right
anchor.isTracked
anchor.handSkeleton != nil
indexFingerTip.isTracked
```

손 전체가 시야에 들어오도록 하고 조명과 손 가림 상태를 바꿔 보세요. 관절 추적이 끊기면 앱은 커서를 숨기고 진행 중인 체류를 취소합니다.

## 점이 너무 쉽게 또는 어렵게 생김

`ConstellationConfiguration.standard`의 값을 조절합니다.

- 점이 이동 중에도 생기면 `dwellDuration`을 늘리거나 `stabilityRadius`를 줄입니다.
- 손 떨림 때문에 점이 생기지 않으면 `stabilityRadius`를 조금 늘립니다.
- 같은 위치에 점이 반복되면 `rearmDistance`와 `minimumPointDistance`를 늘립니다.
- 다음 점을 찍기 위해 너무 멀리 움직여야 하면 `rearmDistance`를 줄입니다.

한 번에 한 값만 바꾸고 실제 사용 거리에서 반복 확인하는 것이 좋습니다.

## 선의 방향이나 길이가 이상함

RealityKit의 생성 원기둥은 로컬 Y축을 따라 놓입니다. 따라서 중점을 위치로 사용하고 `[0, 1, 0]`에서 두 점의 단위 방향 벡터로 회전해야 합니다. 두 점 사이 거리가 0에 가까우면 선을 생성하지 않습니다.

## 로컬 검증 명령

Xcode 프로젝트의 앱 타깃을 빌드합니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

순수 도메인 로직 테스트를 실행합니다.

```shell
swift test
```

`generic/platform=visionOS` destination을 찾을 수 없다는 메시지가 나오면 Xcode Settings > Components에서 visionOS 플랫폼을 설치하세요.
