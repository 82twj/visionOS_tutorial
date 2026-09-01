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
        ├── DwellDetector ── 확정 위치
        ├── ExistingPointConnectionDetector ── 모든 기존 점 스냅
        ├── ConstellationModel ── 별자리별 노드 + 엣지 + 활성 노드
        └── ConstellationRenderer ── 흰색 점·선·커서·연결 안내
```

## 계층별 책임

### 앱과 Scene

`HandConstellationApp`은 제어용 `WindowGroup`과 손 추적용 `ImmersiveSpace`를 선언합니다. `AppModel`은 두 Scene이 공유해야 하는 몰입 상태, 추적 상태, 그리기 상태, 별자리와 점 개수, 초기화 신호를 보관합니다.

`ImmersiveView`는 `RealityView`에 렌더러의 루트 엔티티를 한 번 추가하고, SwiftUI task의 생명 주기에 맞춰 코디네이터를 시작하고 중단합니다.

### 입력 어댑터

`HandTrackingService`는 ARKit API에만 집중합니다. 지원 여부와 권한을 확인하고 오른손 검지 끝을 월드 좌표로 변환합니다.

### 순수 도메인 로직

`DwellDetector`, `ExistingPointConnectionDetector`, `ConstellationModel`은 ARKit이나 RealityKit에 의존하지 않습니다. 그래서 호스트 macOS에서도 체류 경계값, 최근접 목표 고정, 중복 엣지 차단과 별자리 분리를 검증할 수 있습니다.

### 장면 출력

`ConstellationRenderer`는 커서, 점 컨테이너, 선 컨테이너와 연결 안내 컨테이너를 소유합니다. 사용자가 기존 점 가까이에 오면 해당 목표 하나에 흰색 반투명 대상을 표시하고 현재 출발점부터 목표까지 미리보기 선을 보여 줍니다. 모델이 전달한 값만 확정 렌더링하며 ARKit 세션을 알지 못합니다.

## 데이터 흐름

1. provider가 오른손 `HandAnchor`를 방출합니다.
2. service가 검지 끝을 월드 위치로 바꿉니다.
3. 창의 버튼 상태가 그리기 꺼짐이면 입력을 중단합니다.
4. 그리기가 켜진 동안 기존 점 연결 감지기가 가장 가까운 목표를 먼저 검사합니다.
5. 연결이 확정되면 model은 새 점 없이 현재 활성 노드와 기존 노드 사이에 엣지를 추가합니다.
6. 선택한 기존 노드는 새 활성 노드가 되어 다음 가지의 출발점이 됩니다.
7. 기존 점 목표가 없으면 일반 dwell detector가 새 점 위치를 한 번만 방출합니다.
8. model은 새 노드와 활성 노드 사이의 엣지를 계산하며 자기 연결과 중복 엣지를 거부합니다.
9. renderer가 흰색 점과 선, 선택 목표와 미리보기 상태를 루트 엔티티 아래에 반영합니다.

추적이 손실되면 3단계의 진행 상태와 커서만 취소합니다. 이미 확정한 별자리 데이터는 사용자가 초기화하거나 몰입형 공간을 닫기 전까지 유지합니다.

## 설정값 조정

`ConstellationConfiguration.standard`에서 체험의 감도를 한곳에서 조절합니다.

| 설정 | 기본값 | 역할 |
| --- | ---: | --- |
| `dwellDuration` | 0.8초 | 점을 확정하기 위한 체류 시간 |
| `stabilityRadius` | 0.015m | 같은 체류로 인정하는 흔들림 반경 |
| `rearmDistance` | 0.03m | 다음 체류를 허용하기 위한 이동 거리 |
| `connectionSnapDistance` | 0.03m | 기존 점을 연결 목표로 선택하는 진입 반경 |
| `connectionReleaseDistance` | 0.04m | 목표 고정과 진행을 유지하는 해제 반경 |
| `minimumPointDistance` | 0.03m | 너무 가까운 점을 모델에서 거부하는 거리 |
| `maximumPointCount` | 100 | 한 장면에서 허용하는 최대 점 개수 |

실제 기기에서 손 떨림과 사용 거리를 관찰한 뒤 `stabilityRadius`와 `dwellDuration`을 함께 튜닝하세요.
