# Hand Constellation

ARKit의 visionOS Hand Tracking으로 오른손 검지 끝을 인식하고, 공중에 점과 선을 그리는 SwiftUI 튜토리얼 프로젝트입니다. 새 위치에서는 점을 만들고 기존 점에서는 중복 점 없이 선만 다시 연결하므로, 어느 점에서든 가지를 이어 복합적인 별자리를 만들 수 있습니다.

![Hand Constellation 대표 이미지](HandConstellation/HandConstellation.docc/constellation-hero.svg)

## 완성 동작

1. **별자리 그리기 시작**을 바라보고 엄지와 검지를 맞대어 몰입형 공간을 엽니다.
2. 공간은 안전하게 **그리기 꺼짐** 상태로 시작합니다. 창의 **그리기 켜기** 버튼으로 시작합니다.
3. 오른손 검지 끝의 흰색 커서를 원하는 위치에 둡니다.
4. 작은 범위 안에서 약 0.8초 동안 머물면 흰색 점이 생깁니다.
5. 손가락을 3cm 이상 옮긴 다음 다시 머물면 새 점과 현재 출발점 사이에 흰색 선이 생깁니다.
6. 원하는 기존 점의 3cm 안에서 머물면 새 점 없이 기존 점까지 선만 연결됩니다.
7. 연결한 기존 점이 새 출발점이 되므로 그 지점에서 계속 가지를 그릴 수 있습니다.
8. 자기 자신이나 이미 연결된 점에는 중복 선을 만들지 않고 이유를 안내합니다.
9. 창의 **그리기 끄기** 버튼으로 입력을 멈춥니다.
10. 그리기를 다시 켠 뒤 만드는 첫 점은 이전 별자리와 연결되지 않고 새 별자리를 시작합니다.
11. **초기화**로 모든 별자리의 점과 선을 지울 수 있습니다.

## 개발 환경

- Xcode 16 이상과 visionOS SDK
- visionOS 2.0 이상을 실행하는 Apple Vision Pro
- SwiftUI, ARKit, RealityKit
- 실제 손 추적과 권한 검증을 위한 실기기

Xcode Settings > Components에서 visionOS 플랫폼과 필요한 Simulator runtime을 먼저 설치하세요.

## 실행하기

1. `HandConstellation.xcodeproj`를 Xcode에서 엽니다.
2. HandConstellation 타깃의 Signing & Capabilities에서 Team을 선택합니다.
3. `com.example.HandConstellation`을 본인의 고유한 Bundle Identifier로 바꿉니다.
4. Apple Vision Pro를 실행 대상으로 선택하고 앱을 Run합니다.
5. 손 추적 권한을 허용한 뒤 몰입형 공간을 엽니다.

손 추적 사용 설명은 `HandConstellation/Info.plist`에 포함되어 있습니다.

## 프로젝트 구조

```text
HandConstellation/
├── HandConstellationApp.swift        SwiftUI Scene 진입점
├── ControlView.swift                 시작·종료·그리기 전환·초기화 창
├── ImmersiveView.swift               RealityView와 추적 task
├── HandTrackingService.swift         권한·ARKitSession·검지 좌표
├── ConstellationConfiguration.swift  체류·거리·크기 조절 값
├── DwellDetector.swift               체류 상태 머신
├── ExistingPointConnectionDetector.swift  모든 기존 점의 스냅과 연결 체류 판정
├── ConstellationModel.swift          점 노드·선 엣지 그래프 규칙
├── ConstellationRenderer.swift       흰색 점·선·커서·연결 피드백
├── ImmersiveCoordinator.swift        전체 데이터 흐름 연결
└── HandConstellation.docc/           DocC 튜토리얼과 참조 문서
DocumentationTheme/                   확대된 단계·코드 패널용 DocC 렌더 테마
Scripts/                              코드 스냅샷·튜토리얼 이미지 생성과 검증
```

설계 근거와 조사 결과는 [PROJECT_REQUIREMENTS.md](PROJECT_REQUIREMENTS.md), 완성 튜토리얼은 [DocC 카탈로그](HandConstellation/HandConstellation.docc/HandConstellation.md)에서 확인할 수 있습니다.

## 검증하기

호스트 macOS에서 ARKit과 무관한 체류·기존 점 연결·그래프 모델 테스트 23개를 실행합니다.

```shell
swift test
```

visionOS 앱 타깃을 코드 서명 없이 빌드합니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  CODE_SIGNING_ALLOWED=NO \
  build
```

로컬 Xcode에 visionOS platform component가 없고 SDK만 있다면 다음처럼 SDK를 직접 지정해 컴파일할 수 있습니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -target HandConstellation \
  -configuration Debug \
  -sdk xros \
  -arch arm64 \
  CODE_SIGNING_ALLOWED=NO \
  build
```

## DocC 문서 빌드

Xcode의 Product > Build Documentation을 사용하거나 명령줄에서 실행합니다.

```shell
xcodebuild \
  -project HandConstellation.xcodeproj \
  -target HandConstellation \
  -configuration Debug \
  -sdk xros \
  -arch arm64 \
  CODE_SIGNING_ALLOWED=NO \
  docbuild
```

튜토리얼은 7개 Chapter와 19개 실습 페이지로 나뉩니다. Chapter 1~6은 Xcode의 초기 코드에서 시작해 앱을 완성하고, Chapter 7은 Apple Vision Pro에서 권한 허용, 임의 기존 점 연결, 버튼 기반 그리기 전환과 별자리 분리를 확인합니다. 파일 생성은 해당 기능을 구현하는 첫 단계에 포함하고, AppModel·제어창·기존 점 연결은 작은 코드 변경으로 나누어 설명합니다. 각 코드 단계에서 이전 코드와 달라진 줄을 강조합니다. 아키텍처, 체류 판정, 기존 점 스냅, 문제 해결, GitHub Pages 배포 문서도 함께 포함되어 있습니다.

빌드한 아카이브에는 아래 후처리를 실행해야 합니다. 한국어 Chapter 이름의 DocC 경로 충돌로 생기는 다음 링크와 소속 Chapter 오류를 목차 기준으로 바로잡고, 삭제된 파일 준비 페이지 6개의 이전 주소도 연결합니다. GitHub Actions는 이 절차를 자동 실행합니다.

```shell
python3 Scripts/normalize_docc_navigation.py /path/to/HandConstellation.doccarchive
python3 Scripts/verify_tutorial.py --archive /path/to/HandConstellation.doccarchive
```

프로젝트의 `DOCC_TEMPLATE_PATH`가 `DocumentationTheme`을 가리키므로 Xcode와 명령줄 빌드 모두 확대된 단계 카드, 파란 현재 단계 표시, 큰 코드 패널 스타일을 동일하게 적용합니다. 테마의 `js/handconstellation-step-sync.js`는 현재 단계가 바뀔 때 오른쪽 코드 패널만 스크롤해 강조된 줄이 보이도록 맞춥니다. 페이지 자체의 스크롤 위치는 건드리지 않고, 좁은 화면에서는 동작하지 않습니다.

## GitHub Pages 배포

`.github/workflows/documentation.yml`이 `main` 브랜치의 DocC를 정적 사이트로 배포합니다.

1. GitHub 저장소 Settings > Pages에서 Source를 **GitHub Actions**로 선택합니다.
2. 프로젝트를 `main` 브랜치에 push합니다.
3. Actions 탭에서 **Deploy DocC to GitHub Pages**가 완료될 때까지 기다립니다.
4. [배포된 Hand Constellation 튜토리얼](https://82twj.github.io/visionOS_tutorial/tutorials/handconstellationtutorials/)을 엽니다.

workflow는 저장소 이름을 `DOCC_HOSTING_BASE_PATH`로 자동 설정합니다. 사용자/조직 Pages처럼 도메인 루트에 배포할 때는 이 값을 빈 문자열로 바꾸세요.

## 튜토리얼 자료 다시 만들기

튜토리얼의 코드 스냅샷과 개념 그림은 스크립트로 생성합니다. `xcode-info-actual.png`와 `control-window-simulator.png`는 실제 화면 캡처이며 그림 생성기가 덮어쓰지 않습니다. 앱 소스를 고친 뒤에는 다음을 실행해 스냅샷을 다시 만들고 참조를 검사하세요.

```shell
./Scripts/verify-snapshots.sh --generate
```

`./Scripts/verify-snapshots.sh`를 옵션 없이 실행하면 파일을 수정하지 않고 검사만 합니다.

각 파일의 마지막 스냅샷은 실제 앱 소스와 바이트 단위로 같아야 하며, 스크립트가 이를 검사합니다. 그림을 다시 만들려면 다음을 실행합니다.

```shell
python3 Scripts/generate_images.py
```

## 현재 검증 범위

- visionOS SDK 대상 앱과 테스트 번들 컴파일 성공
- `swift test`: 23개 테스트 통과
- DocC 아카이브 경고 없이 빌드 성공
- 코드 스냅샷 95개를 재현하며 모든 Swift 스냅샷이 문법 검사를 통과
- 각 파일의 마지막 스냅샷이 실제 앱 소스와 일치
- 생성된 19개 페이지의 본문·자료 참조·18개 다음 링크·7개 Chapter와 이전 주소 6개를 검사
- 실제 Xcode 26.6 권한 설정과 visionOS 26.5 Simulator 대기 화면을 문서에 포함
- 실제 기기 손 추적 동작과 Chapter 7의 캡처는 Apple Vision Pro에서 최종 확인 필요

2026-09-12 피드백 대응의 범위와 순서는 [상세 수정 계획](TUTORIAL_FEEDBACK_IMPLEMENTATION_PLAN.md), 실제 확인 결과는 [수정 검증 기록](TUTORIAL_FEEDBACK_VERIFICATION.md)을 참고하세요.
