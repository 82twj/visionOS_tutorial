# Hand Constellation visionOS 튜토리얼 요구사항 및 사전 조사

> 조사일: 2026-08-03  
> 상태: 구현 완료 기준 문서  
> 대상: ARKit Hand Tracking, RealityKit, SwiftUI, DocC, GitHub Pages

> 2026-08-18 변경: 몰입형 공간은 그리기 꺼짐 상태로 시작하고, 오른손 주먹 유지 또는 창의 버튼으로 그리기를 전환한다. 그리기를 껐다가 다시 켜면 기존 결과를 유지하면서 새 별자리를 시작한다.

## 1. 문서 목적

이 문서는 Apple Vision Pro에서 검지 끝을 추적해 공중에 별자리 모양을 그리는 SwiftUI 예제와, 그 제작 과정을 설명하는 DocC 튜토리얼의 구현 기준을 정의한다.

이 단계의 범위는 요구사항과 기술 선택을 확정하는 것이다. visionOS 앱, Xcode 프로젝트, DocC 카탈로그, 배포 워크플로 구현은 다음 단계에서 진행한다.

## 2. 사용자가 요청한 핵심 조건

다음 조건은 사용자 요청에서 직접 도출한 필수 조건이다.

1. ARKit의 visionOS Hand Tracking을 사용한다.
2. SwiftUI 기반의 기초 visionOS 앱으로 제작한다.
3. 검지 손가락 끝의 위치를 인식한다.
4. 검지 끝이 한 위치에 오래 머물면 그 위치에 점을 만든다.
5. 다음 점이 만들어지면 이전 점과 새 점 사이를 선으로 연결한다.
6. 점과 선을 반복해서 추가하여 공중에 별자리 형태를 그린다.
7. 구현 전 과정을 초보자가 따라갈 수 있는 단계별 DocC 튜토리얼로 작성한다.
8. 완성된 DocC 문서는 GitHub Pages에 정적 사이트로 배포할 수 있어야 한다.
9. 사용자가 명시적으로 그리기를 켠 동안에만 점을 생성한다.
10. 오른손 주먹을 일정 시간 유지하는 손짓과 창의 버튼으로 그리기를 켜고 끈다.
11. 한 세션에서 여러 별자리를 만들며 서로 다른 별자리 사이에는 선을 연결하지 않는다.

## 3. 완성 경험

사용자는 앱의 기본 창에서 체험을 시작하고 Full Space로 진입한다. 앱이 손 추적 권한을 얻으면 검지 끝의 위치를 계속 관찰한다.

검지 끝이 작은 허용 반경 안에 일정 시간 머무르면 해당 월드 좌표에 별 점이 생성된다. 사용자가 손을 다른 위치로 옮겨 다시 머무르면 두 번째 점이 생성되고, 직전 점에서 새 점까지 선이 추가된다. 같은 방식으로 점과 선을 계속 이어 하나의 별자리를 만든다.

추적이 잠시 끊겨도 이미 만든 별자리는 유지한다. 단, 진행 중이던 머무름 판정은 취소하여 잘못된 점이 생기지 않도록 한다. 사용자는 기본 창의 초기화 버튼으로 모든 점과 선을 지울 수 있다.

## 4. 조사 결과와 기술적 근거

### 4.1 Full Space가 필요한 이유

visionOS는 손 추적처럼 민감한 ARKit 데이터를 Full Space에서만 앱에 제공한다. 따라서 일반 WindowGroup만으로는 이 예제를 완성할 수 없고, SwiftUI 앱에 `ImmersiveSpace`를 선언한 후 `openImmersiveSpace`로 열어야 한다. 권한이 거부되거나 나중에 철회되는 경우도 처리해야 한다.

근거: [Setting up access to ARKit data](https://developer.apple.com/documentation/visionos/setting-up-access-to-arkit-data)

### 4.2 손 추적 API 선택

핵심 입력은 다음 조합으로 구현한다.

- `ARKitSession`: ARKit 데이터 공급자의 실행과 권한 상태를 관리한다.
- `HandTrackingProvider`: 양손의 `HandAnchor` 업데이트를 비동기 시퀀스로 제공한다.
- `HandAnchor`: 손목 기준 월드 변환, 손 방향, 추적 상태와 손 골격을 제공한다.
- `HandSkeleton.JointName.indexFingerTip`: 검지 끝 관절을 선택한다.

`SpatialTrackingSession`은 RealityKit이 앵커 정렬을 대신 관리할 때 유용하다. 이 예제는 검지 끝의 세부 관절 데이터를 읽고 dwell 판정에 사용할 월드 좌표를 직접 계산해야 한다. Apple 문서도 앵커 속성에 완전히 접근하고 변환을 직접 적용하려면 ARKit 세션을 사용할 수 있다고 설명하므로 `ARKitSession`과 `HandTrackingProvider`를 선택한다.

근거:

- [HandTrackingProvider](https://developer.apple.com/documentation/arkit/handtrackingprovider)
- [HandAnchor](https://developer.apple.com/documentation/arkit/handanchor)
- [indexFingerTip](https://developer.apple.com/documentation/arkit/handskeleton/jointname/indexfingertip)
- [SpatialTrackingSession](https://developer.apple.com/documentation/realitykit/spatialtrackingsession)
- [Tracking and visualizing hand movement](https://developer.apple.com/documentation/visionos/tracking-and-visualizing-hand-movement)

### 4.3 검지 끝의 월드 좌표

`HandAnchor.originFromAnchorTransform`은 손목 밑부분에 있는 손 앵커를 월드 원점 좌표계로 옮긴다. `anchorFromJointTransform`은 해당 손 앵커에서 관절까지의 변환이다. 따라서 검지 끝의 월드 변환은 다음 순서로 계산한다.

```swift
let originFromIndexTip =
    handAnchor.originFromAnchorTransform
    * indexFingerTip.anchorFromJointTransform

let position = SIMD3<Float>(
    originFromIndexTip.columns.3.x,
    originFromIndexTip.columns.3.y,
    originFromIndexTip.columns.3.z
)
```

앵커의 `isTracked`, `handSkeleton` 존재 여부, 검지 끝 관절의 추적 상태를 확인한 뒤에만 dwell 입력으로 사용한다. visionOS 26에서는 관절이 가려지거나 조명이 부족할 때 `isTracked`가 `false`가 될 수 있지만 ARKit이 그럴듯한 추정 변환을 계속 제공할 수 있다. 이 예제는 정확한 점 배치가 중요하므로 추적되지 않은 관절은 입력에서 제외하는 쪽을 기본 정책으로 삼는다.

근거:

- [HandAnchor.originFromAnchorTransform](https://developer.apple.com/documentation/arkit/handanchor/originfromanchortransform)
- [HandSkeleton.Joint.anchorFromJointTransform](https://developer.apple.com/documentation/arkit/handskeleton/joint/anchorfromjointtransform)
- [HandSkeleton.Joint.isTracked](https://developer.apple.com/documentation/arkit/handskeleton/joint/istracked)
- [visionOS 26 Release Notes](https://developer.apple.com/documentation/visionos-release-notes/visionos-26-release-notes)

### 4.4 점과 선 렌더링

3D 콘텐츠는 SwiftUI의 `RealityView` 안에서 RealityKit 엔티티로 표시한다.

- 별 점: `MeshResource.generateSphere`로 만든 작은 `ModelEntity`
- 연결선: 두 점 사이 길이를 높이로 사용하는 원기둥 `ModelEntity`
- 별자리 루트: 모든 점과 선을 자식으로 보관하는 하나의 `Entity`

점 `A`와 `B`를 연결하는 원기둥은 다음 값으로 배치한다.

- 위치: `(A + B) / 2`
- 높이: `distance(A, B)`
- 방향: 원기둥의 로컬 Y축이 `normalize(B - A)`를 향하도록 회전

이 방식은 초급 튜토리얼에서 이해하기 쉽고 점의 개수가 많지 않은 예제에 충분하다. 연속 곡선이나 수백 개 이상의 선이 필요한 확장판에서는 Apple의 3D painting 예제처럼 하나의 동적 메시를 갱신하는 방법을 검토한다.

근거: [Creating a 3D painting space](https://developer.apple.com/documentation/visionos/creating-a-painting-space-in-visionos)

### 4.5 권한과 기능 지원 확인

앱 타깃에는 Hands Tracking capability와 사용 목적 문구가 필요하다.

```text
NSHandsTrackingUsageDescription
```

제안 문구:

> 검지 끝의 움직임을 감지해 공중에 별자리 점과 선을 그리기 위해 손 추적을 사용합니다.

세션을 실행하기 전 `HandTrackingProvider.isSupported`를 확인한다. 권한은 기능을 시작할 때 명시적으로 요청하여, 거부 상태와 지원하지 않는 환경을 기본 창에서 설명한다.

이 예제는 손 추적만 사용하므로 plane detection, scene reconstruction 또는 image tracking용 `NSWorldSensingUsageDescription`은 필수가 아니다.

근거:

- [Setting up access to ARKit data](https://developer.apple.com/documentation/visionos/setting-up-access-to-arkit-data)
- [ARKitSession.AuthorizationType.handTracking](https://developer.apple.com/documentation/arkit/arkitsession/authorizationtype/handtracking)

## 5. 기능 요구사항

### FR-01 체험 시작과 종료

- 기본 창에 체험 시작 버튼을 제공한다.
- 시작하면 이름이 정해진 `ImmersiveSpace`를 연다.
- 종료하면 실행 중인 손 추적 작업을 취소하고 Immersive Space를 닫는다.
- 공간 열기 실패 상태를 사용자에게 표시한다.

### FR-02 검지 끝 추적

- `HandTrackingProvider.anchorUpdates`를 지속적으로 소비한다.
- 유효한 `HandAnchor`, `HandSkeleton`, `.indexFingerTip` 관절만 사용한다.
- 손 또는 검지 끝 관절이 추적되지 않으면 해당 프레임은 배치 판단에서 제외한다.
- 추적 손실 시 진행 중인 dwell 후보를 취소한다.

### FR-03 머무름 감지

- 첫 유효 좌표를 dwell 후보 중심으로 저장한다.
- 이후 좌표가 안정 반경 안에 있으면 경과 시간을 누적한다.
- 반경 밖으로 벗어나면 후보 중심과 시작 시간을 새 좌표로 재설정한다.
- 임계 시간에 도달하면 점 배치 이벤트를 한 번만 발생시킨다.
- 점을 만든 직후에는 같은 위치에서 점이 반복 생성되지 않도록 재무장 조건을 둔다.

### FR-04 점 생성

- 첫 번째 확정 좌표에 구 형태의 별 점을 추가한다.
- 점의 월드 위치를 별자리 데이터 배열에도 저장한다.
- 마지막 점과 지나치게 가까운 좌표에는 새 점을 만들지 않는다.
- 점 개수 제한에 도달하면 추가 입력을 막고 안내 상태를 표시한다.

### FR-05 선 생성

- 두 번째 점부터 직전 점과 새 점을 선으로 연결한다.
- 선의 중심, 길이, 회전을 두 점의 좌표로 계산한다.
- 길이가 0에 가까운 선은 생성하지 않는다.
- 선은 점이 추가된 순서만 연결하며 마지막 점과 첫 점을 자동으로 닫지 않는다.

### FR-06 진행 피드백

- 추적 중인 검지 끝에 작은 커서 또는 미리보기 점을 표시한다.
- dwell 진행 상태를 크기, 링 또는 색 변화로 보여준다.
- 진행 피드백은 점 확정 여부를 색상 하나에만 의존하지 않는다.
- 권한 거부, 미지원 환경, 추적 중단과 실행 오류를 기본 창에 표시한다.

### FR-07 초기화

- 초기화 명령은 모든 점, 선, 저장 좌표와 dwell 상태를 제거한다.
- 초기화 후 바로 새 별자리를 그릴 수 있다.

### FR-08 그리기 상태와 여러 별자리

- 몰입형 공간은 그리기 꺼짐 상태로 시작한다.
- 오른손 주먹을 0.6초 유지하거나 창의 버튼을 눌러 그리기를 켜고 끈다.
- 주먹이 감지되면 진행 중인 dwell 후보를 즉시 취소한다.
- 한 번의 주먹 유지에서는 상태를 한 번만 전환하며, 손을 다시 펼친 뒤 재인식한다.
- 그리기를 끄면 현재 별자리를 마치고 기존 점과 선은 유지한다.
- 다시 켠 뒤의 첫 점은 새 별자리의 시작점이며 이전 별자리와 연결하지 않는다.
- 종료 동작은 Immersive Space를 닫기 전에 그리기를 먼저 끈다.

## 6. 제안하는 초기 상수

아래 값은 구현 시작값이며 Apple Vision Pro 실제 기기 테스트에서 조정해야 한다.

| 항목 | 초기값 | 목적 |
| --- | ---: | --- |
| dwell 시간 | 0.8초 | 의도적인 머무름과 자연스러운 움직임 구분 |
| 안정 반경 | 0.015m | 손 떨림 허용 |
| 점 사이 최소 거리 | 0.030m | 중복 점과 너무 짧은 선 방지 |
| 재무장 이동 거리 | 0.030m | 같은 위치에서 반복 생성 방지 |
| 별 점 반지름 | 0.008m | 팔 길이 거리에서 식별 가능한 시작 크기 |
| 연결선 반지름 | 0.0025m | 점보다 가늘게 표현 |
| 최대 점 개수 | 100개 | 엔티티 무제한 증가 방지 |
| 주먹 유지 시간 | 0.6초 | 의도적인 상태 전환과 순간적인 손 접힘 구분 |

단위는 RealityKit과 ARKit의 월드 좌표 기준인 미터를 사용한다. 상수는 한 구성 타입에 모아 튜토리얼 독자가 쉽게 조절할 수 있게 한다.

## 7. dwell 상태 머신

머무름 감지는 ARKit과 분리된 순수 Swift 타입으로 구현한다.

```text
idle
  └─ 유효 좌표 수신 → dwelling(candidate, startTime)

dwelling
  ├─ 안정 반경 안 → 시간 누적
  ├─ 임계 시간 도달 → committed(position) → coolingDown
  ├─ 반경 밖 → 새 candidate로 dwelling 재시작
  └─ 추적 손실 → idle

coolingDown
  ├─ 재무장 거리 이상 이동 → dwelling
  └─ 추적 손실 → idle
```

시간 계산에는 프레임 수가 아니라 단조 증가 시계를 사용한다. 이렇게 하면 업데이트 빈도가 바뀌어도 dwell 시간이 달라지지 않고 단위 테스트에서 시간을 주입할 수 있다.

## 8. 제안 아키텍처

| 구성요소 | 책임 |
| --- | --- |
| `HandConstellationApp` | WindowGroup과 ImmersiveSpace 선언 |
| `AppModel` | 공간 열림 상태, 사용자 메시지, 초기화 명령 관리 |
| `HandTrackingService` | ARKitSession 실행, 권한·지원 여부 확인, 검지 좌표 스트림 생성 |
| `DwellDetector` | 안정 반경, 시간 임계값, 재무장 상태 관리 |
| `FistHoldDetector` | 주먹 유지, 1회 전환과 손을 펼친 뒤 재활성화 관리 |
| `ConstellationModel` | 별자리별 점 배열과 점·선분 추가 규칙 관리 |
| `ConstellationRenderer` | RealityKit 점·선·커서 엔티티 생성과 제거 |
| `ControlView` | 시작, 종료, 초기화와 상태 표시 |
| `ImmersiveView` | RealityView 구성과 생명주기 연결 |

ARKit 업데이트 수신 작업과 RealityKit 엔티티 변경의 생명주기를 Immersive Space에 묶는다. 공간을 닫은 뒤 백그라운드 작업이 남지 않도록 SwiftUI `.task` 취소를 전파한다. Swift 6 동시성 검사를 고려해 사용자 상태와 엔티티 변경은 MainActor 경계에서 수행하고, 순수 dwell 계산은 프레임워크 타입에 의존하지 않게 유지한다.

## 9. 손 선택 정책

사용자 요청에는 왼손·오른손 지정이 없다. 초급 예제의 복잡도를 낮추기 위한 기본안은 다음과 같다.

- MVP: 오른손 검지 끝만 점 배치 입력으로 사용한다.
- UI와 오류 메시지에서 오른손 사용을 명시한다.
- 확장 단계에서 왼손, 오른손 또는 양손을 선택하는 설정을 추가한다.

양손을 동시에 허용하면 두 개의 dwell 상태, 입력 경쟁과 점 순서 결정 규칙이 필요하다. 접근성을 위해 최종 구현 전에 아래 미결정 사항에서 손 선택 정책을 확정해야 한다.

## 10. 비기능 요구사항

### 안정성과 성능

- 손 추적 업데이트마다 새 메시나 재질을 만들지 않는다.
- 커서 엔티티는 한 번 만들고 위치와 표시 상태만 갱신한다.
- 점과 선의 공용 메시·재질은 재사용한다.
- 비정상적으로 짧은 벡터와 NaN 좌표를 거부한다.
- 앱이 비활성화되거나 Immersive Space가 닫히면 추적 작업을 정리한다.

### 개인정보 보호

- 손 좌표는 체험 중 메모리에만 유지한다.
- 분석 서버나 외부 저장소로 손 데이터를 전송하지 않는다.
- 앱 종료 후 별자리나 손 좌표를 자동 복원하지 않는다.
- 권한 사용 목적을 기능에 맞는 쉬운 문장으로 설명한다.

### 안전과 사용성

- 사용자가 앉거나 안전한 공간에서 팔이 닿는 범위 안에 그리도록 안내한다.
- 실제 벽이나 물체 가까이에 점을 찍도록 유도하지 않는다.
- 추적되지 않는 동안 커서를 숨겨 오래된 위치를 현재 위치처럼 보이지 않게 한다.
- 점 확정 시 시각 피드백을 제공하고, 선택 사항으로 짧은 공간 음향 피드백을 고려한다.

## 11. DocC 튜토리얼 요구사항

DocC는 Markdown 기반 문서와 튜토리얼 지시문을 컴파일하여 Xcode 문서 뷰어와 웹에서 볼 수 있는 문서를 만든다. 앱 타깃은 internal과 public 심볼을 문서화할 수 있으므로 예제 앱의 핵심 타입에도 `///` 문서 주석을 추가한다.

근거:

- [Writing documentation](https://developer.apple.com/documentation/xcode/writing-documentation)
- [Writing symbol documentation in your source files](https://developer.apple.com/documentation/xcode/writing-symbol-documentation-in-your-source-files)
- [Swift-DocC directives](https://swiftlang.github.io/swift-docc/documentation/swiftdocc/directives/)

### 제안 목차

1. 완성 결과와 아키텍처 이해
2. visionOS 프로젝트와 DocC 카탈로그 생성
3. WindowGroup과 ImmersiveSpace 연결
4. Hands Tracking capability와 권한 문구 설정
5. ARKitSession과 HandTrackingProvider 시작
6. 검지 끝의 월드 좌표 계산
7. dwell 상태 머신 구현과 테스트
8. RealityKit으로 별 점 만들기
9. 두 점 사이에 3D 선 만들기
10. 진행 커서, 오류 상태와 초기화 기능 추가
11. Apple Vision Pro에서 검증하고 상수 조정
12. DocC 빌드 및 GitHub Pages 배포

### DocC 산출물 구조안

```text
HandConstellation.docc/
├── HandConstellation.md
├── HandConstellation.tutorials
├── BuildingHandConstellation.tutorial
├── Articles/
│   ├── Architecture.md
│   ├── DwellDetection.md
│   ├── Troubleshooting.md
│   └── GitHubPagesDeployment.md
└── Resources/
    ├── finished-experience.png
    ├── hand-coordinate-spaces.png
    └── dwell-state-machine.png
```

실제 파일 배치는 Xcode가 생성한 documentation catalog 구조와 DocC 링크 검증 결과에 맞춰 조정한다. 각 튜토리얼 단계는 전체 파일을 반복 제시하지 않고, 변경되는 코드와 그 이유를 먼저 설명한 뒤 완성 파일을 참조하도록 구성한다.

## 12. GitHub Pages 정적 배포 조사

이 프로젝트는 Swift Package가 아니라 visionOS 앱 타깃을 문서화하므로 `swift package generate-documentation`보다 `xcodebuild docbuild`를 사용한다. Apple은 `xcodebuild docbuild`로 `.doccarchive`를 만들 수 있고, Xcode 14.3 이후 생성한 아카이브를 일반 정적 파일 서버에 호스팅할 수 있다고 설명한다.

프로젝트 Pages 주소가 `https://<user>.github.io/<repository>/` 형태이면 `<repository>`가 hosting base path가 된다. 빌드 시 `DOCC_HOSTING_BASE_PATH=<repository>`를 전달하여 CSS, 데이터와 심볼 링크가 저장소 하위 경로를 올바르게 가리키게 한다.

배포 워크플로의 기본 흐름은 다음과 같다.

1. macOS 러너에서 저장소를 체크아웃한다.
2. 사용할 Xcode 버전을 선택한다.
3. `xcodebuild docbuild`로 visionOS 앱의 `.doccarchive`를 생성한다.
4. 아카이브 내용을 Pages 업로드 디렉터리로 복사한다.
5. `actions/configure-pages`로 Pages 메타데이터를 구성한다.
6. `actions/upload-pages-artifact`로 정적 파일을 업로드한다.
7. `actions/deploy-pages`로 `github-pages` 환경에 배포한다.

GitHub의 현재 안내에 따르면 배포 작업에는 최소 `pages: write`와 `id-token: write` 권한이 필요하다. 배포 전 저장소 Settings > Pages의 Source를 GitHub Actions로 설정해야 한다.

근거:

- [Distributing documentation to other developers](https://developer.apple.com/documentation/xcode/distributing-documentation-to-other-developers)
- [DOCC_HOSTING_BASE_PATH build setting](https://developer.apple.com/documentation/xcode/build-settings-reference#DocC-Archive-Hosting-Base-Path)
- [Publishing to GitHub Pages — Swift-DocC Plugin](https://swiftlang.github.io/swift-docc-plugin/documentation/swiftdoccplugin/publishing-to-github-pages/)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## 13. 테스트 및 완료 기준

### 순수 로직 테스트

- 안정 반경 안에서 0.8초 미만 머무르면 점 이벤트가 발생하지 않는다.
- 0.8초 이상 머무르면 점 이벤트가 정확히 한 번 발생한다.
- dwell 중 안정 반경을 벗어나면 타이머가 재시작된다.
- 추적 손실 입력을 받으면 dwell 후보가 취소된다.
- 확정 직후 같은 위치에서는 두 번째 이벤트가 발생하지 않는다.
- 재무장 거리 이상 이동한 뒤에는 다음 점을 만들 수 있다.
- 마지막 점과 최소 거리보다 가까운 점은 거부된다.

### 앱 수동 검증

- 권한을 허용하면 오른손 검지 커서가 손을 따라온다.
- 권한을 거부하면 앱이 중단되지 않고 해결 안내를 표시한다.
- 첫 dwell에서 점 하나만 생긴다.
- 두 번째 dwell에서 점과 연결선이 생긴다.
- 세 번째 이후 점이 직전 점과 순서대로 연결된다.
- 손을 가리거나 시야 밖으로 옮기면 잘못된 점이 생성되지 않는다.
- 초기화하면 점, 선과 진행 상태가 모두 제거된다.
- Immersive Space를 반복해서 열고 닫아도 추적 작업이나 엔티티가 중복되지 않는다.

Simulator는 창 UI, 공간 전환과 렌더링 검증에 사용하고, 실제 손 추적 정확도와 dwell 상수는 Apple Vision Pro에서 최종 검증한다. Apple도 Simulator가 실제 기기의 모든 기능과 성능을 재현하지 않으므로 기능 자체는 물리 기기에서 확인하도록 안내한다.

근거: [Running your app on simulated or physical devices](https://developer.apple.com/documentation/xcode/running-your-app-on-simulated-or-physical-devices)

### 문서 및 배포 검증

- 앱과 테스트 타깃이 오류 없이 빌드된다.
- `xcodebuild docbuild`가 오류 없이 완료된다.
- DocC의 해결되지 않은 심볼 링크와 누락 리소스 경고가 없다.
- 로컬에서 랜딩 페이지, 튜토리얼, 코드 링크와 이미지가 열린다.
- GitHub Pages의 저장소 하위 경로에서 CSS와 이미지가 정상 로드된다.
- 랜딩 페이지뿐 아니라 `/documentation/...`과 `/tutorials/...` 깊은 링크도 열린다.

## 14. 현재 작업공간 조사

2026-08-03 확인 결과:

- 작업 경로: 프로젝트 루트
- 기존 파일: 없음
- Git 저장소: 아직 초기화되지 않음
- 설치된 Xcode: Xcode 26.6, build 17F113
- 설치된 visionOS SDK: visionOS 26.5
- 설치된 visionOS Simulator SDK: visionOS 26.5
- Swift: Apple Swift 6.3.3
- 현재 `xcode-select` 경로: `/Library/Developer/CommandLineTools`

전체 Xcode는 `/Applications/Xcode.app`에 설치되어 있지만 기본 개발자 디렉터리는 Command Line Tools를 가리킨다. 이후 명령줄 빌드에서는 Xcode 개발자 디렉터리를 명시하거나 사용자가 `xcode-select` 설정을 변경해야 한다. 저장소 이름과 GitHub Pages URL은 아직 알 수 없으므로 hosting base path는 배포 단계에서 확정한다.

## 15. 범위에서 제외하는 항목

첫 번째 버전에는 다음 기능을 포함하지 않는다.

- 실제 천문 별자리 자동 인식 또는 이름 판정
- 마지막 점과 첫 점의 자동 연결
- 여러 개의 별자리 레이어 관리
- 앱 재실행 후 별자리 영구 저장
- CloudKit, 네트워크 공유 또는 SharePlay
- 눈 추적 데이터 접근
- 장면 재구성 또는 실제 표면에 점 고정
- 사용자 정의 셰이더와 고급 파티클 효과
- App Store 배포 자동화

## 16. 구현 전에 확정할 정보

다음 항목은 현재 합리적인 기본안을 제시할 수 있지만 사용자 결정 또는 실제 저장소 정보가 필요하다.

| 항목 | 제안 기본안 | 필요한 결정 시점 |
| --- | --- | --- |
| 제품 및 Xcode 프로젝트 이름 | `HandConstellation` | 프로젝트 생성 전 |
| Bundle Identifier | `com.example.HandConstellation` 임시값 | 프로젝트 생성 전 |
| 최소 지원 버전 | visionOS 2.0 | 프로젝트 생성 전 |
| 입력 손 | 오른손 우선, 왼손은 확장 단계 | 손 추적 구현 전 |
| immersion style | `.mixed` | ImmersiveSpace 구현 전 |
| UI 언어 | 한국어, 코드 식별자는 영어 | DocC 작성 전 |
| GitHub 소유자와 저장소 이름 | 미정 | Pages 워크플로 작성 전 |
| Pages 공개 방식 | GitHub Actions | 배포 설정 전 |
| 실제 Vision Pro 테스트 가능 여부 | 미정 | dwell 상수 확정 전 |

## 17. 다음 단계 제안

1. 위 미결정 정보 중 프로젝트 이름, Bundle Identifier, 입력 손 정책을 확정한다.
2. Xcode visionOS App 프로젝트와 테스트 타깃을 생성한다.
3. 가장 먼저 프레임워크와 무관한 `DwellDetector` 및 단위 테스트를 구현한다.
4. ImmersiveSpace와 HandTrackingProvider를 연결한다.
5. 점과 선 렌더링을 구현하고 실제 기기에서 상수를 조정한다.
6. 코드가 동작하는 순서에 맞춰 DocC 튜토리얼을 작성한다.
7. GitHub 저장소 정보가 정해지면 Pages workflow와 hosting base path를 추가한다.
