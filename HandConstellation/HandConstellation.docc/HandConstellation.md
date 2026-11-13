# ``HandConstellation``

visionOS의 ARKit 손 추적과 RealityKit으로 공중에 점을 찍고 선으로 이어 별자리를 그립니다.

## Overview

Hand Constellation은 오른손 검지 끝을 커서로 씁니다. 빈 곳에 검지를 잠시 멈추면 흰 점이 찍히고, 다음 점을 찍을 때마다 앞의 점과 선으로 이어집니다. 이미 찍은 점에서 다시 멈추면 새 점 없이 선만 추가되고, 그 점에서 다음 선을 이어 그릴 수 있습니다.

입력은 제어창의 **그리기 켜기**·**그리기 끄기** 버튼으로 켜고 끕니다. 그리기를 껐다가 다시 켜면 다음 점부터 새 별자리가 시작되므로, 한 번 실행하는 동안 별자리를 여러 개 그릴 수 있습니다. **초기화**는 모든 별자리를 지웁니다.

튜토리얼은 스타터 프로젝트에서 시작합니다. 앱 상태(`AppModel`), 제어창(`ControlView`), 설정값(`ConstellationConfiguration`), 별자리 데이터 모델(`ConstellationModel`), 기존 점 연결 감지기(`ExistingPointConnectionDetector`)는 스타터에 들어 있고, 다음 공간 컴퓨팅 코드를 직접 작성합니다.

1. `ARKitSession`과 `HandTrackingProvider`로 오른손 관절 업데이트를 받습니다.
2. 손 앵커 변환과 검지 끝 관절 변환을 곱해 검지 끝의 월드 좌표를 구합니다.
3. `DwellDetector`가 검지가 한곳에 머물렀는지 판단해 점을 한 번만 찍습니다.
4. `ConstellationRenderer`가 점과 선을 RealityKit 엔티티로 그립니다.
5. `ImmersiveCoordinator`와 `ImmersiveView`가 손 추적, 머무르기 판정, 렌더링을 몰입형 공간의 생명주기에 묶습니다.

과정은 5개 Chapter로 되어 있습니다. Chapter 1–4는 Mac과 visionOS Simulator에서 진행하고, 실제 손 추적과 그리기는 Chapter 5에서 Apple Vision Pro로 확인합니다.

> Important: ARKit 손 추적은 몰입형 공간이 열려 있을 때만 데이터를 보냅니다. Simulator에서는 손 추적을 쓸 수 없으므로 실제 동작은 Apple Vision Pro에서 확인하세요.

## Topics

### 시작하기

- <doc:HandConstellationTutorials>
- <doc:BuildingHandConstellation>
- <doc:ReadingTheStarterCode>
- <doc:RunningOnVisionPro>

### 설계 이해하기

- <doc:Architecture>
- <doc:DwellDetection>

### 검증과 배포

- <doc:Troubleshooting>
- <doc:GitHubPagesDeployment>
