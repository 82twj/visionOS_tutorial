# 앱 구조 이해하기

추적 데이터가 RealityKit 엔티티가 되기까지의 책임과 데이터 흐름을 살펴봅니다.

## Overview

Hand Constellation은 프레임마다 바뀌는 ARKit 입력과 오래 유지되는 별자리 상태를 분리합니다. 이 구조는 추적이 잠시 끊기거나 렌더링 방식을 바꾸더라도 체류 판정과 점 연결 규칙을 독립적으로 시험할 수 있게 합니다.

```text
HandTrackingProvider
        │ HandAnchor
        ▼
HandTrackingService ── 월드 검지 위치
        ▼
ImmersiveCoordinator
        ├── FistHoldDetector ── 그리기 켜기/끄기
        ├── DwellDetector ── 확정 위치
        ├── ConstellationModel ── 별자리별 점 + 선택적 선분
        └── ConstellationRenderer ── RealityKit 엔티티
```

## 계층별 책임

### 앱과 Scene

`HandConstellationApp`은 제어용 `WindowGroup`과 손 추적용 `ImmersiveSpace`를 선언합니다. `AppModel`은 두 Scene이 공유해야 하는 몰입 상태, 추적 상태, 그리기 상태, 별자리와 점 개수, 초기화 신호를 보관합니다.

`ImmersiveView`는 `RealityView`에 렌더러의 루트 엔티티를 한 번 추가하고, SwiftUI task의 생명 주기에 맞춰 코디네이터를 시작하고 중단합니다.

### 입력 어댑터

`HandTrackingService`는 ARKit API에만 집중합니다. 지원 여부와 권한을 확인하고, 오른손 검지 끝 관절을 월드 좌표로 변환합니다. 다른 계층에는 `HandAnchor` 대신 `SIMD3<Float>` 위치를 전달합니다.

### 순수 도메인 로직

`FistHoldDetector`, `DwellDetector`, `ConstellationModel`은 ARKit이나 RealityKit에 의존하지 않습니다. 그래서 호스트 macOS에서도 Swift Package 테스트를 실행해 손짓의 1회 전환과 재활성화, 체류 경계값, 추적 손실, 별자리 분리, 최소 거리, 최대 점 개수를 검증할 수 있습니다.

### 장면 출력

`ConstellationRenderer`는 커서, 점 컨테이너, 선 컨테이너를 소유합니다. 모델이 전달한 값만 렌더링하며 ARKit 세션이나 체류 시간을 알지 못합니다.

## 데이터 흐름

1. provider가 오른손 `HandAnchor`를 방출합니다.
2. service가 손가락 관절의 접힘 비율로 주먹 여부를 판정하고 검지 끝을 월드 위치로 변환합니다.
3. coordinator가 주먹 상태와 단조 증가 시각을 `FistHoldDetector`에 전달합니다.
4. 주먹을 0.6초 유지하면 그리기 상태가 한 번 전환됩니다. 그리기를 끌 때 진행 중인 체류를 취소하고 현재 별자리를 마칩니다.
5. 그리기가 켜진 동안 coordinator가 검지 위치를 `DwellDetector`에 전달합니다.
6. detector가 체류 완료 위치를 한 번만 방출합니다.
7. model이 점을 현재 별자리에 저장하고 같은 별자리 안에서만 이전 점과의 선분을 계산합니다.
8. renderer가 점과 선택적 선을 루트 엔티티 아래에 추가합니다.

추적이 손실되면 3단계의 진행 상태와 커서만 취소합니다. 이미 확정한 별자리 데이터는 사용자가 초기화하거나 몰입형 공간을 닫기 전까지 유지합니다.

## 설정값 조정

`ConstellationConfiguration.standard`에서 체험의 감도를 한곳에서 조절합니다.

| 설정 | 기본값 | 역할 |
| --- | ---: | --- |
| `dwellDuration` | 0.8초 | 점을 확정하기 위한 체류 시간 |
| `stabilityRadius` | 0.015m | 같은 체류로 인정하는 흔들림 반경 |
| `rearmDistance` | 0.03m | 다음 체류를 허용하기 위한 이동 거리 |
| `minimumPointDistance` | 0.03m | 너무 가까운 점을 모델에서 거부하는 거리 |
| `maximumPointCount` | 100 | 한 장면에서 허용하는 최대 점 개수 |
| `fistHoldDuration` | 0.6초 | 그리기 상태 전환에 필요한 주먹 유지 시간 |
| `fistFingerExtensionRatio` | 1.45 | 손가락이 손목 쪽으로 접힌 것으로 판단하는 비율 |

실제 기기에서 손 떨림과 사용 거리를 관찰한 뒤 `stabilityRadius`와 `dwellDuration`을 함께 튜닝하세요.
