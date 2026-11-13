# 앱 구조 이해하기

손 추적 데이터가 RealityKit 엔티티가 되기까지 어떤 타입을 거치는지 살펴봅니다.

## Overview

Hand Constellation은 매 프레임 바뀌는 ARKit 입력과, 오래 남는 별자리 데이터를 서로 다른 타입에 나눠 둡니다. 덕분에 추적이 잠시 끊겨도 저장된 점과 선은 그대로 남고, 머무르기 판정과 점 연결 규칙은 ARKit이나 RealityKit 없이 따로 시험할 수 있습니다.

```text
HandTrackingProvider
        │ HandAnchor
        ▼
HandTrackingService ── 검지 끝 월드 좌표
        ▼
ImmersiveCoordinator
        ├── ExistingPointConnectionDetector ── 기존 점에 연결할지 판정
        ├── DwellDetector ── 새 점을 찍을 위치
        ├── ConstellationModel ── 별자리별 점과 선, 다음 선의 시작점
        └── ConstellationRenderer ── 흰색 점·선·커서·연결 안내
```

## 파일과 작성 위치

튜토리얼은 스타터 프로젝트에서 시작합니다. spatial computing과 직접 관련된 코드만 직접 작성하고, 나머지 앱 코드는 스타터에 완성된 채로 들어 있습니다.

| 파일 | 스타터 상태 | 작성하는 곳 |
| --- | --- | --- |
| `AppModel`, `ControlView`, `ConstellationConfiguration`, `ConstellationModel`, `ExistingPointConnectionDetector` | 완성본 | 고치지 않고 그대로 씁니다 |
| `Info.plist` | 씬 설정만 있음 | Chapter 1에서 손 추적 사용 목적 추가 |
| `HandTrackingService` | 비어 있음 | Chapter 2 |
| `DwellDetector` | `update`만 비어 있음 | Chapter 3 |
| `ConstellationRenderer` | 비어 있음 | Chapter 3 |
| `ImmersiveCoordinator`, `ImmersiveView` | 비어 있음 | Chapter 4 |
| `HandConstellationApp` | `WindowGroup`만 있음 | Chapter 4에서 `ImmersiveSpace` 추가 |

## 타입별 역할

### 앱과 씬

`HandConstellationApp`은 제어창용 `WindowGroup`과 손 추적용 `ImmersiveSpace`를 선언합니다. 두 씬은 같은 `AppModel`을 받습니다. `AppModel`에는 공간이 열렸는지, 손 추적 상태, 그리기 켜짐 여부, 별자리·점·선 개수, 초기화 요청 번호가 들어 있습니다.

`ImmersiveView`는 `RealityView`에 렌더러의 루트 엔티티를 한 번 추가하고, `.task`에서 코디네이터를 실행합니다. 공간이 닫히면 task가 취소되면서 추적도 멈춥니다. 그리기 상태와 초기화 요청 번호가 바뀌면 `.onChange`로 코디네이터에 알립니다.

### 손 추적

`HandTrackingService`는 ARKit만 다룹니다. 손 추적을 지원하는지와 권한을 확인해 세션을 시작하고, 오른손 검지 끝의 위치를 월드 좌표로 바꿉니다.

### ARKit에 의존하지 않는 로직

`DwellDetector`, `ExistingPointConnectionDetector`, `ConstellationModel`은 ARKit도 RealityKit도 가져오지 않습니다. 그래서 Mac에서도 머무르기 시간과 반경, 가장 가까운 목표 유지, 중복 선 막기, 별자리 나누기를 단위 테스트로 확인할 수 있습니다.

### 장면 그리기

`ConstellationRenderer`는 커서, 점, 선, 연결 안내를 담을 엔티티를 루트 엔티티 아래에 가지고 있습니다. 기존 점 가까이에 가면 그 점 하나를 반투명 흰색으로 강조하고, 지금 선이 시작될 점에서 목표까지 미리보기 선을 보여 줍니다. 렌더러는 코디네이터가 넘겨준 값만 그리며 ARKit 세션은 알지 못합니다.

## 한 프레임에서 일어나는 일

1. provider가 손 앵커를 보내면 코디네이터는 오른손 앵커만 처리합니다.
2. 제어창의 그리기 상태를 먼저 반영합니다. 그리기가 꺼져 있으면 여기서 멈춥니다.
3. 서비스가 검지 끝을 월드 좌표로 바꿉니다. 좌표를 얻지 못하면 진행 중인 머무르기만 취소합니다.
4. 기존 점 연결 감지기가 지금 별자리의 점 중에서 목표를 찾습니다. 목표에 머무르는 동안에는 새 점 판정으로 넘어가지 않습니다.
5. 연결이 끝나면 모델은 새 점 없이 지금 시작점과 목표 점 사이에 선을 하나 추가하고, 목표 점을 다음 선의 시작점으로 삼습니다. 이미 선으로 이어진 점이면 선을 더하지 않고 안내만 보여 줍니다.
6. 기존 점 목표가 없으면 머무르기 감지기가 새 점 위치를 한 번만 내보냅니다.
7. 모델은 새 점을 저장하고, 시작점이 있으면 두 점을 잇는 선을 만듭니다. 같은 별자리의 점과 3cm보다 가까운 점은 받지 않습니다.
8. 렌더러가 점과 선, 목표 강조와 미리보기 선을 루트 엔티티 아래에 반영합니다.

추적이 끊기면 두 감지기의 진행 상태를 취소하고 커서와 연결 안내를 숨깁니다. 이미 만든 별자리는 사용자가 초기화하거나 몰입형 공간을 닫을 때까지 남아 있습니다.

## 설정값

체험의 감도는 `ConstellationConfiguration.standard` 한 곳에서 조절합니다.

| 설정 | 기본값 | 쓰임 |
| --- | ---: | --- |
| `dwellDuration` | 0.8초 | 점을 찍거나 기존 점에 연결하기까지 머무르는 시간 |
| `stabilityRadius` | 0.015m | 같은 자리에 머무른다고 보는 흔들림 반경 |
| `rearmDistance` | 0.03m | 점을 찍은 뒤 다음 머무르기를 시작하려면 움직여야 하는 거리 |
| `connectionSnapDistance` | 0.03m | 기존 점을 연결 목표로 고르는 거리 |
| `connectionReleaseDistance` | 0.04m | 고른 목표를 놓아주는 거리 |
| `minimumPointDistance` | 0.03m | 모델이 너무 가까운 새 점을 받지 않는 거리 |
| `maximumPointCount` | 100 | 한 장면에 둘 수 있는 점의 최대 개수 |

실제 기기에서 손 떨림과 팔을 뻗는 거리를 관찰한 뒤 `stabilityRadius`와 `dwellDuration`을 함께 조절해 보세요.
