# 2026-11-14 피드백 반영 수정 계획

피드백 원문과 튜토리얼 위치의 대응은 [피드백 매칭 기록](20261114_FeedBack/FEEDBACK_MATCHING.md)에 있다. 이 문서는 그 피드백을 어떻게 반영할지 정한 실행 계획이자, 작업을 나눠 맡는 서브에이전트가 함께 따르는 명세다.

## 1. 목표와 지킬 것

1. **필수 내용만 튜토리얼로**: WWDC 세션처럼 spatial computing을 배우는 사람이 꼭 알아야 하는 코드(ARKit 손 추적·권한, 관절 좌표 → 월드 좌표, 손 입력을 머무르기로 바꾸는 상태 머신, RealityKit 엔티티·재질·선 회전, RealityView·ImmersiveSpace·`.task` 생명주기, 손 앵커 업데이트 루프)만 직접 작성한다. 나머지 코드(앱 상태, 제어창 UI, 설정값, 별자리 그래프 모델, 기존 점 연결 감지기)는 **스타터 프로젝트**로 제공한다.
2. **Step 정리**: 연속 조작(메뉴 열기 → 항목 선택), 행동과 그 결과(Run → Expected Result), 결과와 문제 해결(Expected Result → 문제가 생겼다면)을 한 Step으로 합친다. 문제 해결과 보충 설명은 Step의 **캡션**(구분선 아래 문단)으로 넣는다.
3. **자연스러운 문장**: AI가 쓴 티가 나는 서식과 표현을 사람이 쓴 설명처럼 바꾼다(아래 4장 문체 기준).
4. **레이아웃 유지**: DocC 테마(`DocumentationTheme`)와 페이지 구조(히어로 → Section 설명·미디어 → 왼쪽 Step 카드·오른쪽 코드/이미지 패널 → 평가 → 다음 페이지)를 바꾸지 않는다. CSS·JS는 수정하지 않는다. 새로 쓰는 요소는 DocC가 원래 지원하는 것(Step 캡션, 표, 이미지·GIF, `projectFiles` 다운로드 버튼)만 쓴다.

수정 전 레이아웃 기준값은 [baseline-layout.json](20261114_FeedBack/verification/baseline-layout.json)에 기록했다(1440×900, 배포본 9bdf436). 모든 페이지가 같은 값이다: 히어로 본문 572px, Section 설명 450px·미디어 450px, Step 열 368px·오른쪽 패널 802px, Step 카드 패딩 28/34px·모서리 24px, Step 본문 19.04px, Step 간격 112px, 코드 17px.

## 2. 사전 검증한 DocC 동작 (scratch 빌드로 확인)

- Step은 **본문 문단 1개 + 미디어 1개(@Image 또는 @Code) + 캡션 문단 1개**까지만 허용된다. 둘째 문단은 미디어가 없어도 캡션이 된다. 셋째 문단·목록·표·`---`는 경고(`--warnings-as-errors`라 빌드 실패)가 난다.
- 캡션은 테마에서 위쪽 1px 구분선 + 본문과 같은 19.04px 글꼴로 그려진다. 피드백의 참고 이미지와 같은 모양이다.
- `@Image`에 GIF를 쓸 수 있다. `@Tutorial(time:, projectFiles: X.zip)`은 히어로에 다운로드 버튼을 만들고 zip을 `downloads/`로 복사한다.
- 코드 강조는 `previousFile`과의 차이로 계산된다. 읽기만 하는 Step에서 특정 줄을 강조하려면, 강조할 줄을 뺀 기준 파일(`HL-*.swift`)을 `previousFile`로 준다.

## 3. 새 구조

### 3.1 Chapter와 페이지 (19 → 12페이지, 7 → 5 Chapter)

| Chapter | 페이지(파일) | 직접 하는 일 |
| --- | --- | --- |
| 1 프로젝트 시작하기 | BuildingHandConstellation「시작하기 전에」 | 완성 동작을 그림·GIF로 보고, 스타터 프로젝트를 내려받는다 |
| | ReadingTheStarterCode「스타터 프로젝트 살펴보고 실행하기」 | 파일 구성 확인, 앱 진입점·AppModel 읽기(강조), Simulator 실행 |
| | AddingHandTrackingPermission「손 추적 권한 설명 추가하기」 | Info 탭에 손 추적 사용 목적 추가 |
| 2 손 추적 구현하기 | StartingTheHandTrackingSession | ARKitSession·HandTrackingProvider·지원/권한 확인 |
| | ConvertingTheFingertipToWorldSpace | 검지 끝 월드 좌표(숫자 예시 추가) |
| 3 점과 선 만들기 | DetectingTheDwell「검지를 잠시 멈추면 점 찍기」 | 스타터의 타입을 읽고 `update` 상태 전환 작성 |
| | RenderingPointsAndLines | RealityKit 엔티티 트리·재질·선 회전 |
| 4 전체 기능 연결하기 | BuildingTheCoordinatorLifecycle「코디네이터로 손 추적과 장면 연결하기」 | 손 앵커 루프·생명주기, 입력 처리 코드 연결(기존 ConnectingTheInputPipeline 흡수) |
| | ConnectingTheRealityViewAndAppScenes | RealityView·`.task`, ImmersiveSpace 등록, 제어창의 공간 열기 코드 읽기, Simulator 확인 |
| 5 Vision Pro에서 실행하기 | RunningOnVisionPro / DrawingTheFirstConstellation / DrawingTheSecondConstellation | 서명·설치·권한, 실제 그리기 확인 |

삭제(스타터로 이동 또는 다른 페이지에 흡수): CreatingTheVisionOSProject, BuildingTheAppModel, BuildingTheControlWindow, CollectingTunableValues, DetectingTheClosure, StoringMultipleConstellations, ConnectingTheInputPipeline. 이전 주소는 `LEGACY_ROUTES`로 리디렉션한다.

| 이전 주소 | 새 주소 |
| --- | --- |
| creatingthevisionosproject, buildingtheappmodel, buildingthecontrolwindow, creatingtheappmodelfile, renamingcontentviewtocontrolview | readingthestartercode |
| collectingtunablevalues, creatingtheinputdetectorfiles | detectingthedwell |
| creatingtheconstellationfiles | renderingpointsandlines |
| detectingtheclosure, storingmultipleconstellations, connectingtheinputpipeline, creatingtheimmersivefiles | buildingthecoordinatorlifecycle |
| creatingthehandtrackingservicefile | startingthehandtrackingsession |

### 3.2 스타터 프로젝트

- 위치: `StarterProject/HandConstellation/` (`HandConstellation.xcodeproj`, `HandConstellation/` 소스 폴더, `README.md`). 배포용 압축본: 카탈로그의 `HandConstellation-Starter.zip`(압축 안 최상위 폴더 `HandConstellation-Starter/`). `Scripts/build_starter_project.py`가 앱 소스·스냅샷에서 스타터 Swift 파일을 만들고 고정 타임스탬프로 zip을 재현 가능하게 만든다.
- Xcode 프로젝트: objectVersion 77(Xcode 16 이상에서 열림), 앱 target 하나, 폴더 동기화 그룹, visionOS 2.0, `com.example.HandConstellation`, **Team 없음**, `GENERATE_INFOPLIST_FILE = YES` + 장면 매니페스트만 있는 `Info.plist`(손 추적 키 없음 — Chapter 1에서 독자가 추가). 개인 정보(팀 ID, 이름이 든 파일 머리말) 넣지 않음.
- 파일 상태:

| 파일 | 스타터 상태 | 작성 위치 |
| --- | --- | --- |
| AppModel, ControlView, ConstellationConfiguration, ConstellationModel, ExistingPointConnectionDetector | 완성본(앱 소스와 동일) | 제공 |
| HandConstellationApp | `WindowGroup`만 있는 상태(= `C02-T03-HandConstellationApp-02.swift`) | Chapter 4에서 ImmersiveSpace 추가 |
| DwellDetector | 타입·속성·init·보조 메서드·`hasFiniteComponents` 확장은 있고 `update`만 없음(= `C04-T07-DwellDetector-00.swift`) | Chapter 3 |
| HandTrackingService, ConstellationRenderer, ImmersiveCoordinator, ImmersiveView | `import Foundation`만 있음 | Chapter 2·3·4 |

- 스타터는 그대로 빌드되고 Simulator에서 제어창(대기·그리기 꺼짐·개수 0)이 뜬다. `hasFiniteComponents`가 스타터에 있으므로 Chapter 2의 좌표 검사는 처음부터 이 도우미를 쓴다(기존 Chapter 4의 되돌아가 고치는 Step 삭제).

### 3.3 스냅샷 (카탈로그에 남는 코드 파일)

| 파일 | 스냅샷 체인(`previousFile` 순서) |
| --- | --- |
| Info.plist | `C01-T04-Info-01.plist`(reset) |
| HandConstellationApp | 읽기: `C02-T03-HandConstellationApp-02` ← `HL-HandConstellationApp-scenes`, `HL-HandConstellationApp-environment` / 작성: `C02-T03-…-02` → `C06-T04-HandConstellationApp-03`(최종) |
| AppModel | 읽기: `C02-T02-AppModel-12`(최종) ← `HL-AppModel-drawing` |
| ControlView | 읽기: `C02-T04-ControlView-14`(최종) ← `HL-ControlView-immersive` |
| HandTrackingService | `C03-T01-…-00` → `C03-T02-…-01` → `02` → `03` → `05` → `06` → `07` → `C03-T03-…-08` → `09` → `10` → `C04-T05-HandTrackingService-19`(최종) |
| ConstellationConfiguration | 읽기: `C04-T02-Configuration-07`(최종) ← `HL-Configuration-dwell` |
| DwellDetector | `C04-T07-DwellDetector-00`(스타터, 읽기 ← `HL-DwellDetector-phase`, `HL-DwellDetector-state`) → `C04-T07-…-01` → `02` → `03` → `04` → `C04-T03-DwellDetector-14`(최종) |
| ConstellationRenderer | `C05-T01-…-00` → `C05-T03-…-02` → `04` → `05` → `06` → `08` → `10` → `11` → `13`(최종) |
| ImmersiveCoordinator | `C06-T01-…-00` → `C06-T02-…-01` → `02` → `03` → `C06-T03-ImmersiveCoordinator-22`(최종) |
| ImmersiveView | `C06-T01-…-00` → `C06-T04-…-01` → `02` → `04`(최종) |

강조 기준 파일 `HL-<파일>-<주제>.swift`는 대상 스냅샷에서 강조할 줄만 뺀 파일이다(`generate_snapshots.py`가 생성). 강조 대상:

- `HL-HandConstellationApp-scenes`: `var body: some Scene {`부터 `.windowResizability(.contentSize)`까지(8–13행).
- `HL-HandConstellationApp-environment`: `@State private var appModel = AppModel()`(6행)과 `.environment(appModel)`(11행).
- `HL-AppModel-drawing`: `DrawingState` enum, `immersiveSpaceID`, `isDrawingEnabled`·`setDrawingEnabled`·`toggleDrawing`(그리기 켜기 버튼이 바꾸는 값).
- `HL-ControlView-immersive`: `openImmersiveSpace`·`dismissImmersiveSpace` 환경 값 두 줄과 `toggleImmersiveSpace()` 메서드 전체.
- `HL-Configuration-dwell`: `dwellDuration`·`stabilityRadius`·`rearmDistance` 세 줄.
- `HL-DwellDetector-phase`: `Phase`·`Snapshot` 선언. `HL-DwellDetector-state`: `State` enum과 기준값·`state` 속성.

삭제할 스냅샷: 위 표에 없는 모든 `C0*` 파일(ContentView, AppModel 00–04, ControlView 00–04, HandConstellationApp 00·01, Info-00, HandTrackingService 04·11, Configuration 00–02, DwellDetector 00–13, ExistingPointConnectionDetector 00–06, ConstellationModel 00–14, Renderer 01·03·07·09·12, ImmersiveView 03). 스타터 완성본 파일(Model, 연결 감지기)은 카탈로그 대신 스타터 일치 검사로 확인한다.

### 3.4 새 그림

| 파일 | 쓰는 곳 | 내용 |
| --- | --- | --- |
| `interaction-overview.gif` | 시작하기 전에 Section 1 미디어 | 검지 커서 → 머무르면 커서가 커지고 점 A → 3cm 이동 후 점 B와 선 → 점 C → 기존 점 A로 가면 강조·미리보기 선 → 선만 추가(점 수 유지). 하단에 점·선 개수 표시. 6–8초 반복, 2MB 이하 |
| `interaction-dwell.png` / `interaction-next-point.png` / `interaction-connect.png` | 시작하기 전에 Section 1의 Step | GIF와 같은 그림체의 장면별 정지 화면 |
| `fingertip-world-example.png` | 월드 좌표 페이지 Section 1 | 회전 없는 숫자 예시: 손 앵커 (0.20, 1.10, −0.50) + 앵커 기준 검지 끝 (0.03, 0.09, −0.08) → 월드 (0.23, 1.19, −0.58) |
| `fingertip-world-rotation.png` | 월드 좌표 페이지 Section 1 | 손을 y축으로 90° 돌린 예시: 같은 앵커 기준 값이 월드에서는 다른 방향이 되므로 더하기가 아니라 곱해야 함 |
| `starter-project-files.png` | 시작하기 전에 Section 2 | 스타터 파일 지도: 제공(완성) / 일부 제공 / 직접 작성 + 작성 Chapter |

기존 그림 중 이전 Chapter 번호·페이지 이름이 들어간 것(예: `prerequisites.png`, `xcode-run-destination.png`, `input-pipeline.png` 등)은 새 Chapter 번호로 고쳐 다시 만든다. 그림 생성은 `Scripts/generate_images.py --only 이름,...`로 필요한 그림만 다시 쓴다.

### 3.5 캡처 이미지 재사용

- 스타터 프로젝트를 연 화면: `capture-next-rv-app.png`(파일 목록 전체 + `WindowGroup`만 있는 앱 진입점).
- Simulator 실행 대상: `capture-c01-r05-confirmed.png`, 실행 결과(제어창 대기 상태): `capture-next-rv-window.png`, 제어창 실제 캡처: `control-window-simulator.png`.
- 빈 파일 열기: `capture-c03-ht-f10.png`(HandTrackingService), `capture-next-cr-f10.png`(Renderer), `capture-next-ic-f10.png`(Coordinator), `capture-next-rv-open.png`(ImmersiveView). `capture-next-dw-open.png`은 빈 DwellDetector라 새 스타터와 맞지 않으므로 쓰지 않는다.
- 빌드 성공: 각 페이지의 `*-build-result.png` 하나만 남기고 `*-build-ready`, `*-build`는 지운다.
- 쓰지 않게 된 이미지는 통합 단계에서 카탈로그에서 지운다(원본은 `TutorialCaptures/`와 git 기록에 남음).

## 4. 문체 기준 (모든 본문 공통)

- 도입부의 `**확인 환경**: / **시작 상태**: / **이번 단계에서 만들 것**:` 세 줄 서식을 없애고, 이 페이지에서 무엇을 만들고 어디서 확인하는지를 1–2문단으로 자연스럽게 쓴다.
- `Expected Result · 결과 확인 —` 같은 영어+한국어 라벨을 쓰지 않는다. 결과는 행동 문장 뒤에 바로 쓴다("…가 보이면 됩니다"). 문제 해결은 캡션에 `**문제가 생겼다면**: …`로 쓴다(사용자가 좋다고 한 형식).
- 다음 단어·표현을 피한다: 계약, 책임, 히스테리시스, 흐름(남발), 확정(→ 점을 찍다·만들다), 재무장, 경계 깜빡임, 유일한 신호, ~의 전부입니다, 핵심 조건입니다, 정상입니다(남발), 구분합니다(남발), 수행합니다, 해당, ~하게 됩니다, 이 Step·이 Section(→ 이 단계·이 부분), 괄호 속 영어 병기 남발, "~입니다."로만 끝나는 단조로운 문장 반복.
- 용어 통일: 머무르기(첫 등장 때만 "머무르기(dwell)"), 커서, 점, 선, 별자리, 제어창, 몰입형 공간, **그리기 켜기**/**그리기 끄기**/**초기화** 버튼.
- 나중에 할 일은 어느 Chapter에서 하는지 적는다(사용자가 좋다고 한 형식). 새 Chapter 번호(1–5)를 쓴다.
- 핵심 API를 처음 설명할 때 Apple 문서 링크를 단다(사용자가 좋다고 한 형식).
- 예시:
  - 전: "감지기의 입력 계약은 호출자가 활성 점과 다른 별자리의 점을 후보에서 제외하는 것입니다." → 후: "감지기에는 지금 그리는 별자리의 점만 후보로 넘깁니다. 방금 찍은 점은 후보에서 빼 둡니다."
  - 전: "4cm 해제 반경을 벗어나기 전에는 목표를 바꾸지 않는 히스테리시스로 경계 깜빡임을 줄입니다." → 후: "한 번 고른 점은 손가락이 4cm 밖으로 나갈 때까지 바꾸지 않습니다. 그래서 가까운 두 점 사이에서 목표가 왔다 갔다 하지 않습니다."
  - 전: "**Expected Result · 결과 확인** — Xcode에서 빌드 오류가 없어야 합니다." → 후: "**Command+B**로 빌드하세요. Build Succeeded가 뜨면 됩니다."

## 5. Step 작성 규칙

1. Step = 본문 문단 1개 + 미디어 0–1개 + 캡션 문단 0–1개. 그 밖의 블록은 쓰지 않는다.
2. 연속 조작은 한 Step으로 합친다. 행동 Step과 결과 Step은 한 Step으로 합친다. 따로 있던 "Expected Result"·"문제가 생겼다면" Step은 없앤다.
3. 코드를 읽기만 하는 Step은 말하는 줄이 강조되도록 `HL-*` 기준 파일을 `previousFile`로 쓴다. 강조가 없는 읽기 Step을 만들지 않는다.
4. 같은 그림을 여러 Step에 반복해서 붙이지 않는다. 그림이 같으면 Step을 합친다.
5. `[capture-…]: # "CAPTURE_…"` 편집용 표시는 Step 맨 끝에 둔다. 합친 Step에는 남긴 이미지에 해당하는 표시 하나만 둔다(Chapter 5의 PENDING 표시는 합친 Step의 최종 결과 표시 하나).
6. 표·긴 설명은 Section의 `@ContentAndMedia`에 둔다.

## 6. 작업 분담 (서브에이전트, Opus)

| 담당 | 범위 | 수정 파일 |
| --- | --- | --- |
| A 스타터·스크립트 | 3.2·3.3, LEGACY_ROUTES, 검증 스크립트, CI에 스타터 빌드 추가, Chapter 끝 상태 빌드 확인 | `StarterProject/`, `Scripts/generate_snapshots.py`, `Scripts/verify_tutorial.py`, `Scripts/normalize_docc_navigation.py`, `Scripts/verify-snapshots.sh`, `Scripts/build_starter_project.py`, `.github/workflows/documentation.yml`, 카탈로그의 `C0*`·`HL-*`·zip |
| B 그림 | 3.4 | `Scripts/generate_images.py`, 카탈로그의 새 그림·고친 그림 |
| C Chapter 1 본문 | 목차, 시작하기 전에, 스타터 살펴보기, 권한 | `HandConstellationTutorials.tutorial`, `BuildingHandConstellation.tutorial`, `ReadingTheStarterCode.tutorial`, `AddingHandTrackingPermission.tutorial`, `HandConstellation.md`, 삭제: `CreatingTheVisionOSProject`, `BuildingTheAppModel`, `BuildingTheControlWindow` |
| D Chapter 2–3 본문 | 손 추적 2페이지, 머무르기, 렌더러 | `StartingTheHandTrackingSession`, `ConvertingTheFingertipToWorldSpace`, `DetectingTheDwell`, `RenderingPointsAndLines`, 삭제: `CollectingTunableValues`, `DetectingTheClosure`, `StoringMultipleConstellations` |
| E Chapter 4–5 본문·문서 | 코디네이터, RealityView, Vision Pro 3페이지, 참고 문서 | `BuildingTheCoordinatorLifecycle`, `ConnectingTheRealityViewAndAppScenes`, `RunningOnVisionPro`, `DrawingTheFirstConstellation`, `DrawingTheSecondConstellation`, `Architecture.md`, `DwellDetection.md`, `Troubleshooting.md`, `GitHubPagesDeployment.md`, 삭제: `ConnectingTheInputPipeline` |
| 메인 | 통합 | 고아 이미지 삭제, README, 전체 빌드·검증, 브라우저 레이아웃 비교, 커밋·배포 |

## 7. 검증

1. `./Scripts/verify-snapshots.sh`(스냅샷·참조·최종본 일치·스타터 일치), `swift test`.
2. 스타터 프로젝트와 Chapter 2·3 끝 상태를 visionOS SDK로 빌드. 앱 target 빌드.
3. `xcodebuild docbuild`(`--warnings-as-errors`) → `normalize_docc_navigation.py` → `verify_tutorial.py --archive`.
4. 로컬에서 테마를 적용한 아카이브를 띄워 1440×900에서 전 페이지를 훑고, 기준값과 레이아웃 지표를 비교한다. 캡션·강조 줄·GIF·다운로드 버튼을 눈으로 확인한다.
5. main에 push → GitHub Actions 배포 성공 → 배포본에서 같은 지표를 다시 비교한다.

결과는 [검증 기록](20261114_FeedBack/verification/VERIFICATION.md)에 남긴다.
