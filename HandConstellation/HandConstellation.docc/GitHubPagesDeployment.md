# GitHub Pages에 문서 배포하기

DocC 아카이브를 정적 사이트로 빌드하고 GitHub Actions로 Pages에 배포합니다.

## Overview

저장소의 `.github/workflows/documentation.yml`은 `main` 브랜치가 갱신될 때 문서를 빌드합니다. `DOCC_HOSTING_BASE_PATH`에 저장소 이름을 전달하므로 프로젝트 Pages의 하위 경로에서도 CSS, JavaScript, 링크가 올바르게 작동합니다.

## 로컬에서 DocC 빌드하기

```shell
xcodebuild docbuild \
  -project HandConstellation.xcodeproj \
  -scheme HandConstellation \
  -destination 'generic/platform=visionOS' \
  -derivedDataPath .build/DerivedData \
  CODE_SIGNING_ALLOWED=NO
```

결과 `.doccarchive`는 `.build/DerivedData/Build/Products` 아래에 생성됩니다. 공유하거나 정적 사이트로 확인하기 전에 다음 절차를 실행하세요. Xcode의 Documentation Viewer만 열면 이 후처리가 적용되지 않습니다.

```shell
python3 Scripts/normalize_docc_navigation.py .build/DerivedData/Build/Products/Debug-xros/HandConstellation.doccarchive
python3 Scripts/verify_tutorial.py --archive .build/DerivedData/Build/Products/Debug-xros/HandConstellation.doccarchive
```

실제 아카이브 경로가 다르면 빌드 로그의 경로를 사용하세요.

## 저장소 설정하기

1. GitHub 저장소의 Settings > Pages를 엽니다.
2. Build and deployment의 Source를 **GitHub Actions**로 선택합니다.
3. 문서와 workflow를 `main` 브랜치에 push합니다.
4. 저장소의 Actions 탭에서 **Deploy DocC to GitHub Pages** 실행을 확인합니다.
5. 완료 후 `https://<계정>.github.io/<저장소>/tutorials/handconstellationtutorials/`을 엽니다.

사용자 또는 조직 Pages 저장소처럼 사이트가 도메인 루트에 배포된다면 workflow의 `DOCC_HOSTING_BASE_PATH` 값을 빈 문자열로 바꿉니다.

## Workflow 단계

배포 workflow는 다음 순서를 사용합니다.

1. 소스 checkout
2. 원문·스냅샷·자료 참조 검사
3. Xcode `docbuild`, 경고를 오류로 처리하고 저장소 이름 기반 hosting base path 설정
4. 목차를 기준으로 다음 링크·Chapter를 정규화하고 이전 주소 6개 연결
5. 생성된 본문·코드·이미지·이동 순서를 검사한 `.doccarchive`만 Pages artifact로 업로드
6. OpenID Connect 토큰으로 GitHub Pages 배포

workflow에는 `pages: write`와 `id-token: write` 권한이 필요합니다. 같은 브랜치에서 여러 배포가 겹치면 concurrency 설정이 이전 실행을 취소하고 최신 문서만 배포합니다.

## 배포 실패 확인

- visionOS destination 오류: runner의 Xcode 버전과 포함 플랫폼을 확인합니다.
- `.doccarchive`를 찾지 못함: Build Documentation 로그에서 catalog가 타깃에 포함되었는지 확인합니다.
- 배포 후 스타일이 깨짐: `DOCC_HOSTING_BASE_PATH`가 저장소 이름과 정확히 일치하는지 확인합니다.
- 404 오류: Pages Source가 GitHub Actions인지, workflow의 deploy job이 성공했는지 확인합니다.
