# ``HandConstellation``

visionOS의 ARKit 손 추적과 RealityKit을 사용해 공중에 점과 선으로 별자리를 그립니다.

## Overview

Hand Constellation은 오른손 검지 끝을 커서로 사용합니다. 사용자가 한 지점에 검지를 일정 시간 머물게 하면 점을 확정하고, 다음 점이 확정될 때 두 점 사이에 선을 만듭니다. 공간은 그리기 꺼짐 상태로 시작하며, 오른손 주먹을 0.6초 유지하거나 창의 버튼을 눌러 그리기를 켜고 끕니다.

그리기를 끄면 진행 중인 체류를 취소하고 현재 별자리를 마칩니다. 다시 켠 뒤 만드는 첫 점은 이전 별자리와 연결되지 않으므로 한 번의 세션에서 여러 별자리를 만들 수 있습니다.

이 샘플은 다음 흐름을 작은 타입들로 나누어 설명합니다.

1. `ARKitSession`과 `HandTrackingProvider`가 오른손 관절 업데이트를 전달합니다.
2. 손 앵커와 검지 끝 관절의 변환을 곱해 월드 좌표를 계산합니다.
3. `FistHoldDetector`가 주먹 유지 손짓을 한 번의 그리기 상태 전환으로 바꿉니다.
4. 그리기가 켜진 동안 `DwellDetector`가 위치의 안정성과 체류 시간을 검사합니다.
5. `ConstellationModel`이 별자리별 점과 선분을 결정합니다.
6. `ConstellationRenderer`가 RealityKit 엔티티를 장면에 추가합니다.

> Important: ARKit 손 추적 데이터는 몰입형 공간에서 사용합니다. 실제 손 추적과 권한 흐름은 Apple Vision Pro에서 확인하세요.

## Topics

### 시작하기

- <doc:HandConstellationTutorials>
- <doc:BuildingHandConstellation>

### 설계 이해하기

- <doc:Architecture>
- <doc:DwellDetection>

### 검증과 배포

- <doc:Troubleshooting>
- <doc:GitHubPagesDeployment>
