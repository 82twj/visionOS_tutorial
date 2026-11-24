# GitHub Pages에 문서 배포하기

DocC 아카이브를 정적 사이트로 빌드하고 GitHub Actions로 Pages에 배포합니다.

## Overview

저장소의 `.github/workflows/documentation.yml`은 `main` 브랜치가 바뀔 때마다 문서를 빌드합니다. `DOCC_HOSTING_BASE_PATH`에 저장소 이름을 넘기므로, 프로젝트 Pages처럼 하위 경로에 배포해도 CSS, JavaScript, 링크가 제대로 동작합니다.

Chapter 1의 <doc:ReadingTheStarterCode> 페이지 위쪽에 있는 **Project files** 버튼은 카탈로그의 `HandConstellation-Starter.zip`을 가리킵니다. DocC가 빌드할 때 이 파일을 아카이브의 `downloads/` 폴더로 복사하므로 따로 올릴 필요가 없습니다.

## 로컬에서 DocC 빌드하기

```shell
xcodebuild docbuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  -derivedDataPath .build/DerivedData \
  CODE_SIGNING_ALLOWED=NO
```

결과 `.doccarchive`는 `.build/DerivedData/Build/Products` 아래에 생깁니다. 공유하거나 정적 사이트로 확인하기 전에 다음 두 명령을 실행하세요. Xcode의 Documentation Viewer로만 열면 이 후처리가 적용되지 않습니다.

```shell
python3 Scripts/normalize_docc_navigation.py .build/DerivedData/Build/Products/Debug-xros/HandConstellation.doccarchive
python3 Scripts/verify_tutorial.py --archive .build/DerivedData/Build/Products/Debug-xros/HandConstellation.doccarchive
```

실제 아카이브 경로가 다르면 빌드 로그에 나온 경로를 쓰세요.

## 앱 소스나 스타터를 고쳤을 때

튜토리얼의 코드 스냅샷(`C0*.swift`), 읽기 Step의 강조 기준 파일(`HL-*.swift`), 스타터 프로젝트(`StarterProject/HandConstellation/`)와 그 zip은 모두 앱 소스에서 만들어집니다. 어느 줄을 어느 Step에서 작성하는지는 `Scripts/generate_snapshots.py`에 적혀 있고, 스타터는 그 0번째 상태입니다. 앱 소스를 고쳤다면 다음 명령으로 모두 다시 만들고 검사합니다.

```shell
./Scripts/verify-snapshots.sh --generate
```

`./Scripts/verify-snapshots.sh`를 옵션 없이 실행하면 아무것도 고치지 않고, 본문의 참조·스냅샷·스타터가 서로 맞는지만 확인합니다. `--builds`를 붙이면 스타터 상태와 코드 Step을 하나씩 적용한 상태를 기기용·Simulator용으로 타입 검사해, 어느 Step에서 멈춰도 경고 없이 빌드되는지 확인합니다.

```shell
./Scripts/verify-snapshots.sh --builds
```

특정 Chapter를 마친 상태의 프로젝트가 필요하면 다음처럼 내보냅니다. `--chapter`에는 0–4를 쓸 수 있고, 0은 스타터 그대로입니다.

```shell
python3 Scripts/build_starter_project.py --export ../HandConstellation-Chapter3 --chapter 3
```

## 저장소 설정하기

1. GitHub 저장소의 Settings > Pages를 엽니다.
2. Build and deployment의 Source를 **GitHub Actions**로 선택합니다.
3. 문서와 workflow를 `main` 브랜치에 push합니다.
4. 저장소의 Actions 탭에서 **Deploy DocC to GitHub Pages** 실행을 확인합니다.
5. 끝나면 `https://<계정>.github.io/<저장소>/tutorials/handconstellationtutorials/`을 엽니다.

사용자나 조직 Pages 저장소처럼 사이트가 도메인 루트에 배포된다면 workflow의 `DOCC_HOSTING_BASE_PATH` 값을 빈 문자열로 바꿉니다.

## Workflow 단계

배포 workflow는 다음 순서로 실행됩니다.

1. 소스 checkout
2. `Scripts/verify-snapshots.sh`로 본문·스냅샷·자료 참조와 스타터 프로젝트가 서로 맞는지 검사
3. 스타터 프로젝트가 그대로 빌드되는지 확인
4. Xcode `docbuild`. 경고를 오류로 처리하고, 저장소 이름으로 hosting base path를 설정
5. 목차 순서에 맞춰 다음 페이지 링크와 Chapter 정보를 정리하고, 삭제하거나 합친 이전 페이지 주소를 새 페이지로 연결
6. 생성된 본문·코드·이미지·이동 순서를 검사한 `.doccarchive`만 Pages artifact로 업로드
7. OpenID Connect 토큰으로 GitHub Pages에 배포

workflow에는 `pages: write`와 `id-token: write` 권한이 필요합니다. 같은 브랜치에서 배포가 겹치면 concurrency 설정이 앞의 실행을 취소하고 최신 문서만 배포합니다. 지금 workflow는 Simulator 테스트(`./Scripts/run-simulator-tests.sh`)와 Step별 타입 검사(`--builds`)를 실행하지 않으므로, 이 둘은 로컬에서 실행합니다.

## 배포가 실패할 때

- visionOS destination 오류: runner의 Xcode 버전과 설치된 플랫폼을 확인합니다.
- 스타터 검사 실패: 앱 소스를 바꾼 뒤 `./Scripts/verify-snapshots.sh --generate`를 실행하지 않았는지 확인합니다.
- "unreferenced catalog assets" 또는 "missing catalog resource": 본문에서 쓰지 않는 파일이 카탈로그에 남았거나, 본문이 참조하는 파일이 없습니다.
- `.doccarchive`를 찾지 못함: Build Documentation 로그에서 카탈로그가 타깃에 들어 있는지 확인합니다.
- 배포 후 스타일이 깨짐: `DOCC_HOSTING_BASE_PATH`가 저장소 이름과 정확히 같은지 확인합니다.
- 404 오류: Pages Source가 GitHub Actions인지, workflow의 deploy job이 성공했는지 확인합니다.
