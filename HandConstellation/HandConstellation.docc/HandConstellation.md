# ``HandConstellation``

visionOS의 ARKit 손 추적과 RealityKit을 사용해 공중에 점과 선으로 별자리를 그립니다.

## Overview

Hand Constellation은 오른손 검지 끝을 커서로 사용합니다. 새 위치에 검지를 머물게 하면 흰색 점과 선을 만들고, 현재 별자리의 어느 기존 점에 머물러도 새 점 없이 선만 다시 연결합니다. 연결한 기존 점이 새 출발점이므로 그 지점에서 가지를 계속 그릴 수 있습니다. 공간은 그리기 꺼짐 상태로 시작하며 창의 버튼으로만 켜고 끕니다.

그리기를 끄면 진행 중인 체류를 취소하고 현재 별자리를 마칩니다. 다시 켠 뒤 만드는 첫 점은 이전 별자리와 연결되지 않으므로 한 번의 세션에서 여러 별자리를 만들 수 있습니다.

이 샘플은 다음 흐름을 작은 타입들로 나누어 설명합니다.

1. `ARKitSession`과 `HandTrackingProvider`가 오른손 관절 업데이트를 전달합니다.
2. 손 앵커와 검지 끝 관절의 변환을 곱해 월드 좌표를 계산합니다.
3. 그리기가 켜진 동안 `DwellDetector`가 위치의 안정성과 체류 시간을 검사합니다.
4. `ExistingPointConnectionDetector`가 모든 기존 점의 최근접 목표 고정과 연결 체류를 일반 점 입력과 분리합니다.
5. `ConstellationModel`이 점 노드와 선 엣지, 현재 출발점과 중복 연결 규칙을 결정합니다.
6. `ConstellationRenderer`가 흰색 점과 선뿐 아니라 선택 목표와 미리보기 선을 장면에 추가합니다.

체류 시간, 안정 반경, 재활성화 거리, 기존 점 스냅 반경과 점·선 크기 같은 조절 값은 `ConstellationConfiguration` 한 곳에 모여 있습니다.

> Important: ARKit 손 추적 데이터는 몰입형 공간에서 사용합니다. 실제 손 추적과 권한 흐름은 Apple Vision Pro에서 확인하세요.

## Topics

### 시작하기

- <doc:HandConstellationTutorials>
- <doc:BuildingHandConstellation>
- <doc:RunningOnVisionPro>

### 설계 이해하기

- <doc:Architecture>
- <doc:DwellDetection>

### 검증과 배포

- <doc:Troubleshooting>
- <doc:GitHubPagesDeployment>
