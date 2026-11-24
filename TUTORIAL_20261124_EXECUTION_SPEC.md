# 2026-11-24 수정 작업 공통 규칙

[점검 결과와 수정 계획](TUTORIAL_20261124_AUDIT_AND_PLAN.md)을 실행할 때 모든 작업자가 따르는 규칙이다. 문체 기준은 [11월 14일 수정 계획](TUTORIAL_20261114_REVISION_PLAN.md) 4장을 그대로 쓴다.

## 건드리지 않는 것

- `CaptureWorkspace/`(사용자가 스테이징해 둔 파일), `20261114_FeedBack/`, `DocumentationTheme/`, 예전 `TUTORIAL_*` 문서, `TutorialCaptures/`.
- 판정 기준값(0.8초, 1.5cm, 3cm, 4cm)과 실제 기기에서의 앱 동작.
- 커밋·push는 메인 세션만 한다. 작업자는 커밋하지 않는다.
- 개인 정보(이름, 계정, 팀 ID, 로컬 경로)를 어떤 파일에도 넣지 않는다.

## 페이지 구성 (목표)

| Chapter | 페이지 (파일) | 형식 |
| --- | --- | --- |
| 1 프로젝트 시작하기 | 시작 글 (`BuildingHandConstellation`) | `@Article` |
| | 스타터 프로젝트 살펴보고 실행하기 (`ReadingTheStarterCode`) | 튜토리얼 |
| | 손 추적 권한 설명 추가하기 (`AddingHandTrackingPermission`) | 튜토리얼 |
| 2 손 추적 구현하기 | `StartingTheHandTrackingSession`, `ConvertingTheFingertipToWorldSpace` | 튜토리얼 |
| | 마무리 글 (`WrapUpHandTracking`) | `@Article` |
| 3 점과 선 만들기 | `DetectingTheDwell`(끝에서 테스트 실행), `RenderingPointsAndLines`(끝에서 `#Preview`) | 튜토리얼 |
| | 마무리 글 (`WrapUpPointsAndLines`) | `@Article` |
| 4 전체 기능 연결하기 | `BuildingTheCoordinatorLifecycle`, `ConnectingTheRealityViewAndAppScenes`(공간 열기 작성, Simulator에서 그려 보기) | 튜토리얼 |
| | 마무리 글 (`WrapUpConnectingTheExperience`) | `@Article` |
| 5 Vision Pro에서 실행하기 | `RunningOnVisionPro`, `DrawingTheFirstConstellation`, `DrawingTheSecondConstellation` | 튜토리얼 |
| | 마무리 글 (`WrapUpHandConstellation`) | `@Article` |

기존 파일 이름은 주소를 지키기 위해 바꾸지 않는다.

## 직접 작성하는 것과 스타터가 주는 것

| 직접 작성 (공간 컴퓨팅 핵심) | 스타터 제공 |
| --- | --- |
| 손 추적 권한 설명 (Info 탭) | 앱 상태 `AppModel`, 제어창 화면, 설정값, 그래프 모델 |
| `HandTrackingService` 전체 | 기존 점 연결 감지기 |
| `DwellDetector.update` | `DwellDetector`의 타입·속성·보조 메서드, 테스트 파일 |
| 렌더러: 엔티티 트리, 점·선·커서, `#Preview` | 렌더러의 기존 점 연결 안내 부분 |
| 코디네이터: 손 앵커 반복문, 시작·초기화·종료, 한 프레임 처리 순서 | 코디네이터의 속성·`init`·안내 문구와 개수를 맞추는 보조 메서드 |
| `ImmersiveView` 전체, `ImmersiveSpace` 등록 | Simulator 전용 입력(제어창의 입력 패드) |
| 제어창의 `openImmersiveSpace`·`dismissImmersiveSpace` 호출 | |

## Step 규칙

- 코드 Step 하나는 메서드 하나, 판단 하나처럼 뜻이 있는 덩어리다. 변경량은 10–30줄을 기준으로 하고 40줄을 넘기지 않는다. 한두 줄짜리 Step을 따로 만들지 않는다.
- 모든 코드 Step은 그 상태로 빌드된다. 썼다가 나중에 통째로 바꾸는 코드를 만들지 않는다.
- Step 본문은 문단 하나, 1–3문장, 150자 이내. "무엇을 하라"를 먼저 쓴다.
- 캡션(두 번째 문단)은 이유를 덧붙일 가치가 있을 때만 쓴다. 1–2문장, 150자 이내. 문제 해결은 `**문제가 생겼다면**:`으로 시작하고, 실제로 막히기 쉬운 Step에만 둔다.
- 모든 Step에 `@Code` 또는 `@Image`가 있다.
- 코드를 읽기만 하는 Step은 강조 기준 파일(`HL-*.swift`)로 설명하는 줄을 강조한다.
- 메뉴 조작, 실행과 결과, 결과와 문제 해결은 한 Step으로 합친다(11월 14일 피드백).
- Step 안에 표, 목록, `---`를 쓰지 않는다(DocC 경고 = 빌드 실패).

## Section·히어로 규칙

- Section 설명은 문단 1–2개, 250자 이내. 표와 목록을 쓰지 않는다. 표로 보여 줄 내용은 그림이나 Step으로 옮긴다.
- 히어로는 문단 1–2개. `@Tutorial(time:)`은 쓰지 않는다.
- 페이지 도입부를 "이 페이지에서는 …합니다" 한 가지 문형으로 시작하지 않는다.

## 퀴즈 규칙

- 코드를 작성하는 8페이지에 3문제씩. 시작 글, 마무리 글, Chapter 5 실습 페이지에는 두지 않는다.
- 보기는 3개(참·거짓형만 2개). 정답은 하나.
- 페이지마다 유형을 섞는다: 이유를 묻는 문제, 코드를 고르는 문제, 상황을 주고 결과를 묻는 문제.
- 오답은 실제로 하기 쉬운 착각으로 만든다. 읽자마자 지워지는 보기는 쓰지 않는다.
- 보기 길이를 비슷하게 맞춘다. 정답 위치는 페이지 안에서 겹치지 않게 섞는다.
- 모든 보기에 한 문장 해설을 단다. 반응 문구는 "맞습니다!"와 "다시 생각해 보세요."
- 그 페이지에서 배운 내용만 묻는다.

## 용어

| 쓰는 말 | 쓰지 않는 말 |
| --- | --- |
| 장면 (SwiftUI `Scene`, RealityKit 장면) | 씬 |
| 몰입형 공간 | 이머시브 스페이스 |
| 제어창 | 컨트롤 창, 제어 창 |
| 머무르기 | 체류, dwell(처음 한 번만 괄호로) |
| 점을 찍다 | 점 확정 |
| 기존 점에 연결 | 닫기, 스냅 |
| `init` | initializer, 이니셜라이저 |
| 손 앵커 | 핸드 앵커 |
| 엔티티 | 개체 |
| 점·선 | 노드·간선(코드 이름을 가리킬 때만 `Node`·`Edge`) |

점 이름은 A·B·C·D로 쓴다. 앱의 점·선·커서는 모두 흰색이다.

## 이미지 규칙

- 실제 캡처는 `capture-*.png`. 스타터 프로젝트(zip을 푼 폴더)로 찍고, 창 모서리 밖은 투명, 포인터·화면 공유 표시·경고·Git 표시가 없어야 한다.
- 개념도는 `Scripts/generate_images.py`가 만든다. 그림 안의 글은 본문·앱 문구와 글자까지 같아야 한다.
- Simulator 화면을 실제 기기 화면처럼 쓰지 않는다. Chapter 5에서 쓸 때는 Simulator 화면이라고 밝힌다.

## DocC 형식 메모 (시험 빌드로 확인)

- 시작 글·마무리 글은 `.tutorial` 파일에 `@Article(time: 5) { @Intro(title:) { … } @ContentAndMedia { … } }`로 쓴다. `time`은 DocC가 요구하므로 넣되, 빌드 후처리(`normalize_docc_navigation.py`)가 화면에서 지운다.
- `@Article`의 `@ContentAndMedia` 안에는 `##`·`###` 제목, 목록, 표, `> Note:`를 쓸 수 있다. `@Image`를 넣으면 글 옆에 그림이 붙고, 없으면 전체 폭으로 나온다. 제목 단위로 `@ContentAndMedia`를 나눈다.
- 튜토리얼 페이지는 `@Tutorial { … }`로 시작한다(`time` 없음). 스타터를 내려받는 페이지만 `@Tutorial(projectFiles: HandConstellation-Starter.zip)`.
- Step 캡션에는 `> Note:`, `> Tip:`, `> Experiment:`를 쓸 수 있다. 작은 라벨과 글로 나온다. 한 Step에 하나만, 꼭 필요할 때만 쓴다. 직접 값을 바꿔 보라는 제안은 `> Experiment:`로 쓴다.
- 퀴즈 보기에는 코드 블록(```swift)을 쓸 수 있다.
- 마무리 글의 구성: `## 배운 내용 돌아보기`(문단 1–2개와 `### 다룬 주제` 목록 4–6개) → `## 더 해 보기`(`### 앱 바꿔 보기` 목록 2–4개, `### 도전 과제` 문단 하나, `### 더 알아보기` Apple 문서·WWDC 세션 링크 2–4개) → `## 다음 단계`(문단 하나).
- 시작 글의 구성: `## 배울 내용`(목록) → `## 완성된 앱`(동작 GIF와 그림) → `## 필요한 것`(목록, Simulator 설치 방법) → `## 진행 순서`(Chapter 표).

## 사실 관계 메모

- 사용 목적 문장(`NSHandsTrackingUsageDescription`)이 없을 때 정확히 어떻게 되는지(거부 처리인지 앱 종료인지)는 Apple 문서에 나와 있지 않다. "권한 요청이 실패합니다"라고 단정하지 말고 "이 항목이 없으면 앱이 손 추적 권한을 받을 수 없습니다"라고 쓴다. 문제 해결에서는 "권한 창이 뜨지 않거나 앱이 바로 종료되면 이 항목을 확인하세요"라고 쓴다.
- ARKit 데이터는 앱이 몰입형 공간(Full Space)을 열었을 때만 들어온다. 근거: [Setting up access to ARKit data](https://developer.apple.com/documentation/visionos/setting-up-access-to-arkit-data).
- 몰입형 공간 안의 `RealityView`와 ARKit은 같은 원점을 쓴다. 그래서 손 앵커에서 구한 월드 좌표를 엔티티의 `position`에 그대로 넣을 수 있다. 이 전제를 좌표 변환 페이지와 `RealityView` 페이지에서 한 문장씩 설명한다.
- Info 탭에서 추가한 권한 문장은 `Info.plist` 파일이 아니라 빌드 설정 `INFOPLIST_KEY_NSHandsTrackingUsageDescription`에 저장된다(실제 프로젝트에서 확인).
- 완성 앱의 커서 크기: 새 점 모드 0.72배 → 1.42배, 기존 점 연결 모드 1.0배 → 1.85배. 본문에 숫자를 쓸 때는 코드와 대조한다.
