# 튜토리얼 개편 감사와 대응표

> 작성일: 2026-08-31
> 근거 문서: [TUTORIAL_REVISION_PLAN.md](TUTORIAL_REVISION_PLAN.md) 11장 1단계
> 대상: 개편 전 `BuildingHandConstellation.tutorial` 1개 페이지, 8개 Section, 78개 Step

> 2026-09-01 후속 개정: 앱 소스와 튜토리얼을 그래프 기반 임의 기존 점 연결, 중간 관절 기반 주먹 1초 끄기, 흰색 단색 렌더링으로 함께 갱신했다. 아래 1~4장은 최초 개편 당시의 감사 기록이며, 5장 이후는 후속 개정 결과를 반영한다.

> 2026-09-01 최종 개정: 주먹 인식과 관련 튜토리얼 2개를 제거하고 제어창 버튼만으로 그리기를 전환한다. 아래 최초 개편 표의 주먹 관련 행은 역사적 기록이다.

## 1. 개편 전 Step 분류

| 기존 Section | Step 수 | 새 파일 생성 | 기존 파일 수정 | 개념 설명 | 실행 | 검증 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. 프로젝트를 만들고 첫 코드 읽기 | 9 | 0 | 1 | 3 | 2 | 3 |
| 2. 앱의 공통 상태 만들기 | 9 | 1 | 8 | 0 | 0 | 0 |
| 3. 창과 몰입형 공간 연결하기 | 9 | 0 | 9 | 0 | 0 | 0 |
| 4. 오른손 검지 끝 추적하기 | 9 | 1 | 8 | 0 | 0 | 0 |
| 5. 머무름을 한 번의 점으로 바꾸기 | 10 | 1 | 9 | 0 | 0 | 0 |
| 6. 주먹으로 그리기를 켜고 끄기 | 8 | 1 | 7 | 0 | 0 | 0 |
| 7. 점, 별자리, 선을 모델링하기 | 11 | 2 | 9 | 0 | 0 | 0 |
| 8. 입력 흐름을 연결하고 확인하기 | 11 | 1 | 6 | 0 | 1 | 3 |
| 합계 | 76 | 7 | 57 | 3 | 3 | 6 |

개편 전 구조의 확인 사항은 다음과 같다.

- 새 파일을 만드는 Step 7개가 모두 기존 파일을 수정하는 Step과 같은 Section 안에 있었다.
- 기기 실행과 완성 동작 검증 Step 4개가 마지막 구현 Section 안에 섞여 있었다.
- 개념 설명만 하는 Step은 3개뿐이고, 나머지는 코드 변경과 설명을 한 Step에서 함께 처리했다.
- `@Chapter`가 1개뿐이라 목차에서 진도를 확인할 수 없었다.

## 2. 기존 Section에서 새 Chapter·Tutorial로 가는 대응표

| 기존 Section | 새 Chapter | 새 튜토리얼 페이지 |
| --- | --- | --- |
| 1 | Chapter 1 | `BuildingHandConstellation`, `CreatingTheVisionOSProject`, `ReadingTheStarterCode`, `AddingHandTrackingPermission` |
| 2 | Chapter 2 | `CreatingTheAppModelFile`, `BuildingTheAppModel` |
| 3 | Chapter 2 | `RenamingContentViewToControlView`, `BuildingTheControlWindow` |
| 4 | Chapter 3 | `CreatingTheHandTrackingServiceFile`, `StartingTheHandTrackingSession`, `ConvertingTheFingertipToWorldSpace` |
| 5 | Chapter 4 | `CreatingTheInputDetectorFiles`, `DetectingTheDwell` |
| 6 | Chapter 4 | `DetectingTheFistHold`, `RecognizingAFistInTheHandSkeleton` |
| 7 | Chapter 5 | `CreatingTheConstellationFiles`, `StoringMultipleConstellations`, `RenderingPointsAndLines` |
| 8 (구현 부분) | Chapter 6 | `CreatingTheImmersiveFiles`, `BuildingTheCoordinatorLifecycle`, `ConnectingTheInputPipeline`, `ConnectingTheRealityViewAndAppScenes` |
| 8 (실행·검증 부분) | Chapter 7 | `RunningOnVisionPro`, `DrawingTheFirstConstellation`, `DrawingTheSecondConstellation` |
| 신규 | Chapter 4 | `CollectingTunableValues` |

## 3. 실제 앱 소스와 개편 전 스냅샷의 차이

개편 전 `S1-`~`S8-` 스냅샷은 실제 앱 소스와 다음 차이가 있었다.

| 항목 | 개편 전 스냅샷 | 실제 앱 소스 | 개편 후 처리 |
| --- | --- | --- | --- |
| 들여쓰기 | 공백 2칸 | 공백 4칸 | 실제 소스와 동일하게 공백 4칸으로 통일 |
| 문서 주석 | 없음 | 모든 타입과 주요 메서드에 `///` | 실제 소스와 동일하게 포함 |
| `Sendable` 준수 | 없음 | `DwellDetector`, `FistHoldDetector`, `ConstellationModel`, `ConstellationConfiguration` | 실제 소스와 동일하게 포함 |
| `precondition` 검사 | 없음 | 각 initializer에 존재 | 실제 소스와 동일하게 포함 |
| `ConstellationConfiguration.swift` | 튜토리얼에 없음 | 앱에 존재하며 세 타입의 기본값이 참조 | Chapter 4에 전용 페이지 2개 추가 |
| `AppModel.statusMessage` | 없음 | 앱에 존재 | Chapter 2에 Step 추가 |
| `ConstellationModel.points` | 없음 | 앱에 존재 | Chapter 5에 포함 |
| `HandTrackingService.anchorPosition` | 없음 | 앱에 존재 | Chapter 4에 포함 |
| `ControlView` 상태 표시 | 축약본 | 200줄 전체 | Chapter 2의 2개 페이지로 분할해 전체 반영 |

개편 후 각 파일의 마지막 스냅샷은 실제 앱 소스와 바이트 단위로 같다. 확인 방법은 다음과 같다.

```shell
./Scripts/verify-snapshots.sh
```

## 4. 계획 대비 의도적으로 조정한 부분

| 계획 | 조정 | 이유 |
| --- | --- | --- |
| `ConstellationConfiguration`을 Chapter 5에 배치 | Chapter 4로 이동 | `DwellDetector`와 `FistHoldDetector`의 기본값이 이 타입을 참조하므로, Chapter 4보다 뒤에 두면 중간 빌드가 깨진다 |
| Chapter 2를 3개 페이지로 구성 | 4개 페이지 | `ControlView.swift`가 200줄이라 한 페이지 5~15분 규칙을 지킬 수 없다 |
| Chapter 4를 3개 페이지로 구성 | 5개 페이지 | 설정값 페이지 2개가 추가되고, 손 골격의 주먹 판정을 별도 페이지로 분리했다 |
| Chapter 6을 3개 페이지로 구성 | 4개 페이지 | `ImmersiveCoordinator.swift`가 187줄이라 생명주기와 입력 파이프라인을 나눴다 |
| 전체 22~25개 페이지 | 27개 페이지 | 시작점 스냅과 도형 닫기를 설명하는 페이지가 추가되었다 |
| `HandConstellationApp`의 씬 연결을 Chapter 6에 배치 | 2회로 분리 | Chapter 2에서 `ContentView`를 `ControlView`로 바꿀 때 진입점도 함께 고쳐야 빌드가 유지된다. `ImmersiveSpace` 씬 추가만 Chapter 6에 남겼다 |

## 5. 실제 앱 소스와 튜토리얼 동시 개정

후속 개정에서는 `HandConstellation/*.swift`, 테스트, 튜토리얼 스냅샷과 개념 이미지를 함께 변경했다. `Info.plist`와 사용자가 별도로 바꾼 Signing Team은 건드리지 않았다. 확인 방법은 다음과 같다.

```shell
git diff --stat -- HandConstellation/*.swift HandConstellation/Info.plist
```

## 6. 실제 기기 캡처 대기 항목

계획 8.3에 따라 다음 이미지는 구조와 파일 이름을 먼저 확정하고 개념도로 채웠다. 공개 전에 실제 캡처로 교체한다.

| 파일 이름 | 필요한 캡처 | 사용 페이지 |
| --- | --- | --- |
| `xcode-new-project-template.png` | Xcode의 visionOS App 템플릿 선택 화면 | `CreatingTheVisionOSProject` |
| `xcode-project-options.png` | Product Name·Interface·Language 입력 화면 | `CreatingTheVisionOSProject` |
| `xcode-project-navigator.png` | Project navigator의 기본 파일 목록 | `ReadingTheStarterCode` |
| `xcode-simulator-hello.png` | Simulator의 기본 앱 실행 결과 | `ReadingTheStarterCode` |
| `xcode-info-tab.png` | Target Info 탭의 권한 항목 추가 위치 | `AddingHandTrackingPermission` |
| `xcode-new-file.png` | New File 메뉴와 Swift File 템플릿 | `CreatingTheAppModelFile` |
| `xcode-file-options.png` | 파일 이름과 Target Membership 화면 | `CreatingTheAppModelFile` |
| `xcode-run-destination.png` | Apple Vision Pro 실행 대상 선택 | `RunningOnVisionPro` |
| `device-permission-prompt.png` | 실제 기기의 손 추적 권한 창 | `RunningOnVisionPro` |
| `device-closed-triangle.png` | 네 점과 다섯 선으로 임의 기존 점을 연결한 그래프 | `DrawingTheFirstConstellation` |
| `closure-snap-feedback.png` | 임의 기존 점 선택, 미리보기와 연결 완료 | `DetectingTheClosure`, `DrawingTheFirstConstellation` |
| `device-second-constellation.png` | 분리된 두 번째 별자리 | `DrawingTheSecondConstellation` |

권한 창 이미지는 실제 시스템 화면을 흉내 내지 않고, 대기 상태임을 이미지 안에 표시한 안내 그림을 사용한다.

## 7. 개편 후 검증 결과

### 확인한 항목

| 항목 | 결과 |
| --- | --- |
| 목차에 7개 Chapter가 순서대로 표시 | 확인 |
| 25개 튜토리얼 페이지가 모두 목차에 연결되고 열림 | 확인 |
| 기존 `BuildingHandConstellation` 식별자 보존 | 확인, Chapter 1의 첫 페이지로 재사용 |
| 새 파일 생성 페이지 5개에 `previousFile` 없음 | 확인 |
| Vision Pro 실행 절차가 Chapter 7에만 존재 | 확인 |
| 모든 `@Code`, `previousFile`, `@Image` 참조 해결 | 검증 스크립트 기준 누락 0 |
| 참조되지 않는 스냅샷·이미지 | 0개 |
| 코드 스냅샷 Swift 문법 검사 | 검증 스크립트 통과 |
| 각 파일 마지막 스냅샷과 실제 앱 소스 일치 | 11개 파일 모두 일치 |
| DocC 빌드 | 오류·경고 없음 |
| `swift test` | 23개 통과 |
| 실제 앱 소스 변경 | 그래프 연결·버튼 전환·흰색 렌더링 반영 |
| 전체 예상 학습 시간 | 210분 |

### 코드 자동 스크롤 검증

DocC 렌더러와 같은 DOM 구조를 만든 테스트 페이지에 실제 배포 스크립트를 그대로 불러 확인했다.

| 상황 | 기대 동작 | 결과 |
| --- | --- | --- |
| 화면보다 짧은 강조 블록 | 코드 패널 중앙 배치 | 300px 패널에서 90px 블록이 105~195px에 배치 |
| 같은 파일의 아래쪽 줄로 이동 | 새 위치로 다시 중앙 배치 | scrollTop 1695 → 2955 |
| 화면보다 긴 강조 블록 | 상단에 12% 여백만 두고 정렬 | 첫 강조 줄이 36px 지점 |
| 강조 줄이 없는 코드 자료 | 코드 상단으로 이동 | scrollTop 0 |
| Step 변화 없이 사용자가 수동 스크롤 | 되돌리지 않음 | scrollTop 700 유지 |
| 다른 Section의 코드 패널 | 영향 없음 | scrollTop 0 유지 |
| 코드가 없는 페이지 | 아무 동작 없음 | 확인, `.code-preview` 자체가 없음 |
| 좁은 화면 | 아무 동작 없음 | 700px에서 데스크톱 코드 패널이 숨겨짐을 실제 페이지에서 확인 |

왼쪽 페이지 자체의 스크롤 위치는 어떤 경우에도 바꾸지 않는다. 스크립트는 `.code-preview` 안쪽 스크롤 컨테이너의 `scrollTop`만 설정한다.

### 남은 항목

- 6장 표의 Xcode 캡처 8개를 실제 화면 캡처로 교체
- Apple Vision Pro 실기기에서 권한 창, 첫 별자리, 두 번째 별자리 캡처 3개 확보
- 위 캡처를 확보한 뒤 Chapter 7의 동작 검증을 실기기에서 1회 수행
