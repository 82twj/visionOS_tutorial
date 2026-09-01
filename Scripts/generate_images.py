#!/usr/bin/env python3
"""Generates the DocC tutorial illustrations as SVG and rasterizes them to PNG.

Every drawing uses the same dark spatial palette as the existing hero art so
that a page mixing old and new figures still reads as one set.
"""

import math
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "HandConstellation" / "HandConstellation.docc"

W, H = 1100, 720
FONT = "-apple-system,'SF Pro Text','Apple SD Gothic Neo',sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Menlo,monospace"

INK = "#f5f7fa"
BODY = "#d7e3eb"
MUTED = "#8faabd"
ACCENT = "#42c8ff"
FOCUS = "#1677ff"
YELLOW = "#ffd14a"
ORANGE = "#ff6a3d"
GREEN = "#32b466"
PANEL = "#111726"
LINE = "#3a4a63"


def t(x, y, s, size=20, fill=BODY, weight=400, anchor="start", font=FONT, opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}"{op}>{escape(s)}</text>'
    )


def rect(x, y, w, h, rx=16, fill="none", stroke=None, sw=2, opacity=None, dash=None):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"']
    if stroke:
        parts.append(f' stroke="{stroke}" stroke-width="{sw}"')
    if opacity is not None:
        parts.append(f' opacity="{opacity}"')
    if dash:
        parts.append(f' stroke-dasharray="{dash}"')
    parts.append("/>")
    return "".join(parts)


def head(x, y, angle, color=ACCENT, size=15):
    """An explicit arrowhead; SVG markers do not survive every rasterizer."""
    return (
        f'<path d="M0 0 L{-size} {size * 0.55} L{-size} {-size * 0.55} z" fill="{color}" '
        f'transform="translate({x} {y}) rotate({angle})"/>'
    )


def arrow(x1, y1, x2, y2, color=ACCENT, sw=5):
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" '
        f'stroke-linecap="round"/>' + head(x2, y2, angle, color)
    )


def card(x, y, w, h, title, lines, accent=ACCENT, fill=PANEL, title_size=25, body_size=19):
    out = [rect(x, y, w, h, 22, fill, accent, 2)]
    out.append(rect(x, y, 6, h, 3, accent))
    out.append(t(x + 26, y + 44, title, title_size, INK, 650))
    cy = y + 84
    for line in lines:
        out.append(t(x + 26, cy, line, body_size, BODY))
        cy += 32
    return "".join(out)


def svg(title, desc, body, w=W, h=H):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
        f'  <title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>\n'
        f'  <defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="#263654"/><stop offset="1" stop-color="#0e111c"/></linearGradient>'
        f'<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="#ffffff" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="#8adfff" stop-opacity=".07"/></linearGradient>'
        f'<marker id="head" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M1 1 L11 6 L1 11 z" fill="{ACCENT}"/></marker>'
        f'<marker id="headw" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M1 1 L11 6 L1 11 z" fill="{MUTED}"/></marker>'
        f'</defs>\n'
        f'  {rect(0, 0, w, h, 44, "url(#bg)")}\n  {body}\n</svg>\n'
    )


def heading(text, sub=None):
    out = t(56, 78, text, 34, INK, 700)
    if sub:
        out += t(56, 116, sub, 20, MUTED)
    return out


def pending_badge():
    """Marks a figure that a real screen capture replaces before publication."""
    label = "실제 캡처 예정"
    w = 190
    return (
        rect(W - w - 56, 46, w, 40, 20, "none", ORANGE, 2, dash="8 6")
        + t(W - w / 2 - 56, 73, label, 18, ORANGE, 600, "middle")
    )


def window_chrome(x, y, w, h, title, accent=LINE):
    """A neutral Xcode-like window frame used for interface diagrams."""
    out = [rect(x, y, w, h, 20, "#0b1120", accent, 2)]
    out.append(f'<path d="M{x} {y+56} h{w}" stroke="{accent}" stroke-width="2"/>')
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        out.append(f'<circle cx="{x+28+i*24}" cy="{y+28}" r="8" fill="{color}"/>')
    out.append(t(x + w / 2, y + 36, title, 19, MUTED, 600, "middle"))
    return "".join(out)


def field(x, y, w, label, value, focused=False, mono=False):
    color = FOCUS if focused else LINE
    out = [t(x, y - 12, label, 17, MUTED)]
    out.append(rect(x, y, w, 46, 10, "#131b2b", color, 3 if focused else 2))
    out.append(t(x + 16, y + 31, value, 19, INK if focused else BODY, 600 if focused else 400,
                 font=MONO if mono else FONT))
    return "".join(out)


FIGURES: dict[str, str] = {}


def figure(name, title, desc, body, w=W, h=H):
    FIGURES[name] = svg(title, desc, body, w, h)


# --- 1. 시작하기 전에 ---------------------------------------------------------

body = [heading("이 과정을 시작하기 전에", "필요한 사전 지식과 확인 환경")]
body.append(card(56, 160, 320, 300, "이미 알고 있어야 함", [
    "Swift 문법과 옵셔널", "struct와 class의 차이", "SwiftUI View와 상태", "Xcode 프로젝트 만들기",
], GREEN))
body.append(card(392, 160, 320, 300, "이 과정에서 설명함", [
    "ARKit 손 추적", "RealityKit 엔티티", "simd 좌표 변환", "체류 판정 상태 머신",
], ACCENT))
body.append(card(728, 160, 316, 300, "확인 환경", [
    "Xcode 16 이상", "visionOS 2.0 이상 SDK", "Simulator: 창 UI 확인", "실기기: 손 추적 검증",
], YELLOW))
body.append(rect(56, 500, 988, 160, 22, "#131b2b", ORANGE, 2))
body.append(t(88, 552, "Simulator에서 확인할 수 없는 것", 24, ORANGE, 650))
body.append(t(88, 594, "ARKit 손 추적은 Apple Vision Pro에서만 동작합니다. Simulator에서는 제어 창과", 20, BODY))
body.append(t(88, 626, "몰입형 공간 열기까지 확인하고, 점과 선 생성은 Chapter 7에서 실기기로 검증합니다.", 20, BODY))
figure("prerequisites", "시작하기 전에",
       "필요한 사전 지식, 과정에서 설명하는 개념, 확인 환경, Simulator 제한을 정리한 표",
       "".join(body))

# --- 2. Xcode 템플릿 선택 -----------------------------------------------------

body = [heading("visionOS App 템플릿 선택", "Xcode > Create New Project"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "Choose a template for your new project"))
tabs = ["multiplatform", "iOS", "macOS", "visionOS", "watchOS", "tvOS"]
tx = 108
for tab in tabs:
    focused = tab == "visionOS"
    w = len(tab) * 12 + 40
    body.append(rect(tx, 246, w, 42, 10, FOCUS if focused else "none",
                     None if focused else LINE, 2))
    body.append(t(tx + w / 2, 274, tab, 18, INK if focused else MUTED,
                  650 if focused else 400, "middle"))
    tx += w + 14
body.append(f'<path d="M108 314 h884" stroke="{LINE}" stroke-width="2"/>')
items = [("App", True), ("Window", False), ("Immersive Space", False), ("Game", False)]
ix = 132
for label, focused in items:
    color = FOCUS if focused else LINE
    body.append(rect(ix, 356, 176, 176, 18, "#131b2b", color, 4 if focused else 2))
    body.append(rect(ix + 52, 392, 72, 72, 16, color, None, opacity=0.9 if focused else 0.3))
    body.append(t(ix + 88, 502, label, 19, INK if focused else MUTED,
                  650 if focused else 400, "middle"))
    ix += 208
body.append(t(132, 578, "visionOS 탭을 고른 다음 App 템플릿을 선택하고 Next를 누릅니다.", 20, BODY))
figure("xcode-new-project-template", "visionOS App 템플릿 선택",
       "Xcode 새 프로젝트 창에서 visionOS 탭과 App 템플릿이 파란색으로 강조된 화면",
       "".join(body))

# --- 3. 프로젝트 옵션 ---------------------------------------------------------

body = [heading("프로젝트 이름과 언어 설정", "Choose options for your new project"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "Choose options for your new project"))
body.append(field(132, 262, 560, "Product Name", "HandConstellation", focused=True, mono=True))
body.append(field(132, 372, 380, "Interface", "SwiftUI", focused=True))
body.append(field(556, 372, 136, "Language", "Swift", focused=True))
body.append(field(132, 482, 560, "Initial Scene", "Window"))
body.append(rect(736, 250, 256, 320, 18, "#131b2b", LINE, 2))
body.append(t(764, 292, "확인할 것", 21, INK, 650))
for i, line in enumerate([
    "이름은 정확히", "HandConstellation", "Interface는 SwiftUI", "Language는 Swift",
    "저장 위치를 기억",
]):
    body.append(t(764, 336 + i * 34, line, 18, BODY, font=MONO if i == 1 else FONT))
figure("xcode-project-options", "프로젝트 옵션 입력",
       "Product Name에 HandConstellation, Interface에 SwiftUI, Language에 Swift를 지정한 화면",
       "".join(body))

# --- 4. Project navigator ----------------------------------------------------

body = [heading("Xcode가 만들어 준 파일", "Project navigator"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "HandConstellation.xcodeproj"))
body.append(rect(104, 246, 340, 360, 16, "#0e1524", LINE, 2))
tree = [
    ("HandConstellation", 0, False),
    ("HandConstellationApp.swift", 1, True),
    ("ContentView.swift", 1, True),
    ("Assets.xcassets", 1, False),
    ("Info.plist", 1, False),
    ("Preview Content", 1, False),
]
for i, (label, depth, focused) in enumerate(tree):
    y = 292 + i * 48
    if focused:
        body.append(rect(112, y - 28, 324, 40, 9, FOCUS, None, opacity=0.28))
    body.append(t(126 + depth * 26, y, label, 18, INK if focused else BODY,
                  650 if focused else 400, font=MONO))
body.append(card(476, 250, 264, 170, "앱 진입점", [
    "@main이 붙은 타입", "처음 열 창을 정함",
], ACCENT))
body.append(card(476, 442, 264, 164, "첫 화면", [
    "Hello, world! 표시", "곧 ControlView가 됨",
], ACCENT))
body.append(arrow(452, 322, 470, 322))
body.append(arrow(452, 370, 470, 500))
body.append(rect(772, 250, 220, 356, 18, "#131b2b", LINE, 2))
body.append(t(796, 294, "이번 페이지는", 20, INK, 650))
body.append(t(796, 334, "읽기만 합니다.", 20, BODY))
body.append(t(796, 380, "코드를 아직", 20, BODY))
body.append(t(796, 412, "바꾸지 않습니다.", 20, BODY))
figure("xcode-project-navigator", "Project navigator의 기본 파일",
       "Project navigator에서 앱 진입점 파일과 ContentView.swift가 파란색으로 강조된 화면",
       "".join(body))

# --- 5. Simulator 실행 --------------------------------------------------------

body = [heading("Simulator에서 기본 앱 확인", "Apple Vision Pro Simulator"), pending_badge()]
body.append(rect(72, 168, 470, 470, 24, "#0b1120", LINE, 2))
body.append(t(104, 216, "Xcode 도구 막대", 19, MUTED, 600))
body.append(rect(104, 240, 406, 62, 14, "#131b2b", FOCUS, 3))
body.append(f'<path d="M126 271 l0 -16 l18 16 l-18 16 z" fill="{GREEN}"/>')
body.append(t(166, 278, "HandConstellation", 19, INK, 650, font=MONO))
body.append(t(336, 278, "Apple Vision Pro", 18, ACCENT, 600))
body.append(t(104, 348, "실행 대상에서 Apple Vision Pro", 20, BODY))
body.append(t(104, 380, "Simulator를 고르고 Run을 누릅니다.", 20, BODY))
body.append(rect(104, 424, 406, 176, 18, "#131b2b", LINE, 2))
body.append(t(130, 468, "이 단계의 목적", 20, INK, 650))
body.append(t(130, 508, "손 추적이 아니라 프로젝트가", 19, BODY))
body.append(t(130, 540, "정상적으로 만들어졌는지만", 19, BODY))
body.append(t(130, 572, "확인합니다.", 19, BODY))
body.append(rect(578, 168, 450, 470, 30, "#070b15", ACCENT, 2, opacity=0.6))
body.append(rect(640, 300, 326, 206, 26, "url(#glass)", "#d8f5ff", 2))
body.append(f'<circle cx="732" cy="376" r="26" fill="none" stroke="{ACCENT}" stroke-width="6"/>')
body.append(f'<path d="M706 376 h52 M732 350 v52" stroke="{ACCENT}" stroke-width="6"/>')
body.append(t(812, 386, "Hello, world!", 26, INK, 650, "middle"))
body.append(t(803, 560, "기본 창이 보이면 성공입니다.", 20, MUTED, anchor="middle"))
figure("xcode-simulator-hello", "Simulator의 기본 앱 실행 결과",
       "실행 대상으로 Apple Vision Pro Simulator를 고르고 Hello, world! 창을 확인하는 화면",
       "".join(body))

# --- 6. Info 탭 ---------------------------------------------------------------

body = [heading("손 추적 권한 설명 추가", "TARGETS > HandConstellation > Info"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "Custom visionOS Target Properties"))
tabs = ["General", "Signing & Capabilities", "Resource Tags", "Info", "Build Settings"]
tx = 108
for tab in tabs:
    focused = tab == "Info"
    w = len(tab) * 11 + 34
    body.append(t(tx + w / 2, 258, tab, 18, INK if focused else MUTED,
                  650 if focused else 400, "middle"))
    if focused:
        body.append(f'<path d="M{tx} 274 h{w}" stroke="{FOCUS}" stroke-width="4"/>')
    tx += w + 18
body.append(f'<path d="M108 288 h884" stroke="{LINE}" stroke-width="2"/>')
rows = [
    ("Application Scene Manifest", "Dictionary", "(2 items)", False),
    ("Privacy - Hand Tracking Usage Description", "String", "검지 끝의 움직임을…", True),
    ("Supported interface orientations", "Array", "(1 item)", False),
]
for i, (key, kind, value, focused) in enumerate(rows):
    y = 330 + i * 76
    if focused:
        body.append(rect(108, y - 30, 884, 62, 12, FOCUS, None, opacity=0.24))
        body.append(rect(108, y - 30, 884, 62, 12, "none", FOCUS, 3))
    body.append(t(136, y + 8, key, 19, INK if focused else BODY, 650 if focused else 400))
    body.append(t(660, y + 8, kind, 18, MUTED))
    body.append(t(790, y + 8, value, 18, ACCENT if focused else MUTED))
body.append(f'<circle cx="128" cy="588" r="17" fill="{FOCUS}"/>')
body.append(t(128, 597, "+", 26, "#fff", 700, "middle"))
body.append(t(164, 596, "+ 를 눌러 항목을 추가하고 Value에 설명 문장을 입력합니다.", 20, BODY))
figure("xcode-info-tab", "Target Info 탭의 권한 항목",
       "Target Info 탭에서 Privacy - Hand Tracking Usage Description 항목이 파란색으로 강조된 표",
       "".join(body))

# --- 7. New File 메뉴 ---------------------------------------------------------

body = [heading("새 Swift 파일 만들기", "File > New > File from Template"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "Choose a template for your new file"))
body.append(rect(108, 246, 250, 360, 16, "#0e1524", LINE, 2))
for i, group in enumerate(["visionOS", "iOS", "macOS", "Other"]):
    focused = i == 0
    y = 290 + i * 46
    if focused:
        body.append(rect(116, y - 26, 234, 38, 9, FOCUS, None, opacity=0.28))
    body.append(t(140, y, group, 18, INK if focused else MUTED, 650 if focused else 400))
templates = [("Swift File", True), ("SwiftUI View", False), ("Unit Test Case", False)]
ix = 392
for label, focused in templates:
    color = FOCUS if focused else LINE
    body.append(rect(ix, 300, 190, 190, 18, "#131b2b", color, 4 if focused else 2))
    body.append(rect(ix + 60, 336, 70, 88, 12, "none", color, 3))
    body.append(t(ix + 95, 462, label, 19, INK if focused else MUTED,
                  650 if focused else 400, "middle"))
    ix += 214
body.append(t(392, 556, "Swift File을 선택하면 빈 파일에 import 한 줄만 들어갑니다.", 20, BODY))
figure("xcode-new-file", "New File 템플릿 선택",
       "새 파일 만들기 창에서 visionOS 그룹과 Swift File 템플릿이 파란색으로 강조된 화면",
       "".join(body))

# --- 8. 파일 이름과 Target Membership ----------------------------------------

body = [heading("파일 이름과 Target Membership", "Save as"), pending_badge()]
body.append(window_chrome(72, 168, 956, 470, "Save As"))
body.append(field(132, 268, 560, "Save As", "AppModel.swift", focused=True, mono=True))
body.append(field(132, 378, 560, "Where", "HandConstellation"))
body.append(t(132, 480, "Targets", 17, MUTED))
body.append(rect(132, 496, 560, 108, 12, "#131b2b", FOCUS, 3))
body.append(f'<rect x="158" y="518" width="28" height="28" rx="7" fill="{FOCUS}"/>')
body.append('<path d="M164 532 l6 7 l12 -14" stroke="#fff" stroke-width="4" fill="none" '
            'stroke-linecap="round" stroke-linejoin="round"/>')
body.append(t(202, 540, "HandConstellation", 20, INK, 650, font=MONO))
body.append(f'<rect x="158" y="560" width="28" height="28" rx="7" fill="none" '
            f'stroke="{LINE}" stroke-width="2"/>')
body.append(t(202, 582, "HandConstellationTests", 20, MUTED, font=MONO))
body.append(rect(736, 268, 256, 336, 18, "#131b2b", LINE, 2))
body.append(t(764, 312, "체크가 빠지면", 20, INK, 650))
body.append(t(764, 352, "파일이 앱에 포함되지", 19, BODY))
body.append(t(764, 384, "않아 빌드에서", 19, BODY))
body.append(t(764, 416, "찾을 수 없다는 오류가", 19, BODY))
body.append(t(764, 448, "납니다.", 19, BODY))
figure("xcode-file-options", "파일 이름과 Target Membership",
       "파일 이름을 AppModel.swift로 입력하고 HandConstellation 타깃에 체크한 저장 화면",
       "".join(body))

# --- 9. 손 골격과 indexFingerTip ---------------------------------------------

joints = {
    "wrist": (300, 590),
    "indexKnuckle": (352, 396),
    "indexTip": (380, 236),
    "middleKnuckle": (430, 392),
    "middleTip": (470, 226),
    "ringKnuckle": (500, 410),
    "ringTip": (546, 262),
    "littleKnuckle": (560, 442),
    "littleTip": (598, 320),
    "thumbKnuckle": (232, 500),
    "thumbTip": (150, 424),
}
bones = [
    ("wrist", "indexKnuckle"), ("indexKnuckle", "indexTip"),
    ("wrist", "middleKnuckle"), ("middleKnuckle", "middleTip"),
    ("wrist", "ringKnuckle"), ("ringKnuckle", "ringTip"),
    ("wrist", "littleKnuckle"), ("littleKnuckle", "littleTip"),
    ("wrist", "thumbKnuckle"), ("thumbKnuckle", "thumbTip"),
]
body = [heading("오른손 골격과 검지 끝 관절", "HandAnchor.handSkeleton")]
for a, b in bones:
    (x1, y1), (x2, y2) = joints[a], joints[b]
    hot = {a, b} <= {"wrist", "indexKnuckle", "indexTip"}
    body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{ACCENT if hot else LINE}" stroke-width="{7 if hot else 5}" '
                f'stroke-linecap="round"/>')
for name, (x, y) in joints.items():
    hot = name in ("wrist", "indexKnuckle", "indexTip")
    body.append(f'<circle cx="{x}" cy="{y}" r="{15 if name == "indexTip" else 11}" '
                f'fill="{YELLOW if name == "indexTip" else (ACCENT if hot else "#5c6c86")}" '
                f'stroke="{"#fff1a8" if name == "indexTip" else "none"}" stroke-width="4"/>')
body.append(t(300, 640, ".wrist", 20, ACCENT, 600, "middle", font=MONO))
body.append(t(326, 400, ".indexFingerKnuckle", 19, ACCENT, 600, "end", font=MONO))
body.append(t(380, 206, ".indexFingerTip", 21, YELLOW, 650, "middle", font=MONO))
body.append(card(700, 190, 344, 200, "이 과정에서 쓰는 관절", [
    ".indexFingerTip 은 점 위치",
    "오른손 검지 끝 하나만",
    "그리기 입력에 사용",
], YELLOW))
body.append(card(700, 418, 344, 220, "각 관절이 주는 것", [
    "isTracked: 신뢰 가능 여부",
    "anchorFromJointTransform:",
    "손 앵커 기준 4×4 변환",
], ACCENT))
figure("hand-skeleton-joints", "오른손 골격과 검지 끝 관절",
       "손목과 다섯 손가락 관절을 이은 골격 그림에서 검지 끝 관절이 노란색으로 강조된 도해",
       "".join(body))

# --- 10. 좌표 변환 ------------------------------------------------------------

body = [heading("두 변환을 곱해 월드 좌표 만들기", "originFromAnchor × anchorFromJoint")]
body.append(card(56, 180, 300, 190, "손 앵커 변환", [
    "originFromAnchorTransform",
    "월드 원점 → 손 앵커",
], ACCENT))
body.append(t(384, 290, "×", 44, INK, 700, "middle"))
body.append(card(412, 180, 300, 190, "관절 변환", [
    "anchorFromJointTransform",
    "손 앵커 → 검지 끝",
], ACCENT))
body.append(t(740, 290, "=", 44, INK, 700, "middle"))
body.append(card(768, 180, 276, 190, "월드 변환", [
    "월드 원점 → 검지 끝",
], YELLOW))
body.append(rect(56, 412, 988, 246, 22, "#131b2b", LINE, 2))
body.append(t(88, 462, "결과 행렬에서 위치만 꺼내기", 24, INK, 650))
for i, col in enumerate(["columns.0", "columns.1", "columns.2", "columns.3"]):
    x = 96 + i * 176
    focused = i == 3
    body.append(rect(x, 492, 156, 132, 14, "#0e1524", FOCUS if focused else LINE, 4 if focused else 2))
    body.append(t(x + 78, 524, col, 18, INK if focused else MUTED, 650 if focused else 400,
                  "middle", font=MONO))
    body.append(t(x + 78, 562, "회전·크기" if not focused else "위치", 19,
                  MUTED if not focused else YELLOW, 400 if not focused else 650, "middle"))
    if focused:
        body.append(t(x + 78, 600, "x, y, z", 20, YELLOW, 650, "middle", font=MONO))
body.append(t(816, 540, "네 번째 열의 x, y, z가", 19, BODY))
body.append(t(816, 572, "RealityKit에서 쓸", 19, BODY))
body.append(t(816, 604, "월드 위치입니다.", 19, BODY))
figure("world-transform-math", "손 앵커 변환과 관절 변환의 곱",
       "두 개의 4×4 변환을 곱해 얻은 행렬의 네 번째 열에서 x, y, z 위치를 꺼내는 과정 그림",
       "".join(body))

# --- 11. 조절 가능한 값 -------------------------------------------------------

body = [heading("한곳에 모으는 조절 값", "ConstellationConfiguration")]
groups = [
    ("체류 판정", GREEN, [
        ("dwellDuration", "0.8초"),
        ("stabilityRadius", "0.015 m = 1.5cm"),
        ("rearmDistance", "0.030 m = 3cm"),
    ]),
    ("점과 선", YELLOW, [
        ("minimumPointDistance", "0.030 m = 3cm"),
        ("pointRadius", "0.006 m = 6mm"),
        ("lineRadius", "0.0015 m = 1.5mm"),
        ("cursorRadius", "0.005 m = 5mm"),
    ]),
]
x = 56
for title, color, rows in groups:
    h = 108 + len(rows) * 74
    body.append(rect(x, 170, 320, h, 22, PANEL, color, 2))
    body.append(rect(x, 170, 6, h, 3, color))
    body.append(t(x + 26, 214, title, 25, INK, 650))
    for i, (key, value) in enumerate(rows):
        y = 262 + i * 74
        body.append(t(x + 26, y, key, 17, color, 600, font=MONO))
        body.append(t(x + 26, y + 30, value, 19, BODY))
    x += 336
body.append(rect(56, 596, 988, 62, 16, "#131b2b", ACCENT, 2))
body.append(t(88, 634, "ARKit과 RealityKit의 거리 단위는 미터입니다. 0.015는 1.5cm를 뜻합니다.",
              20, BODY))
figure("tunable-values", "조절 가능한 설정값",
       "체류 판정과 점·선 두 묶음으로 나눈 설정값과 미터 단위 환산 표",
       "".join(body))

# --- 12. 체류 상태 머신 -------------------------------------------------------

body = [heading("체류 판정 상태 머신", "DwellDetector.State")]
states = [("idle", 150, 320, MUTED), ("dwelling", 520, 320, ACCENT), ("coolingDown", 880, 320, YELLOW)]
for label, cx, cy, color in states:
    body.append(f'<circle cx="{cx}" cy="{cy}" r="92" fill="#131b2b" stroke="{color}" stroke-width="4"/>')
    body.append(t(cx, cy + 8, label, 22, color, 650, "middle", font=MONO))
body.append(arrow(246, 320, 422, 320))
body.append(t(334, 288, "위치가 들어옴", 18, BODY, anchor="middle"))
body.append(arrow(616, 320, 782, 320))
body.append(t(699, 288, "0.8초 유지", 18, BODY, anchor="middle"))
body.append(f'<path d="M880 412 C 840 520, 580 520, 522 416" fill="none" stroke="{ACCENT}" '
            f'stroke-width="5" stroke-linecap="round"/>' + head(522, 416, -119, ACCENT))
body.append(t(700, 528, "3cm 이상 이동", 18, BODY, anchor="middle"))
body.append(f'<path d="M470 236 C 520 168, 600 178, 604 258" fill="none" stroke="{ACCENT}" '
            f'stroke-width="5" stroke-linecap="round"/>' + head(604, 258, 87, ACCENT))
body.append(t(548, 158, "1.5cm 벗어나면 타이머 재시작", 18, BODY, anchor="middle"))
body.append(f'<path d="M470 402 C 380 490, 240 470, 176 396" fill="none" stroke="{MUTED}" '
            f'stroke-width="4" stroke-linecap="round"/>' + head(176, 396, -131, MUTED, 13))
body.append(t(324, 494, "추적 손실", 18, MUTED, anchor="middle"))
body.append(rect(56, 566, 988, 96, 18, "#131b2b", LINE, 2))
body.append(t(88, 606, "점은 dwelling 에서 coolingDown 으로 넘어가는 그 한 프레임에만 확정됩니다.",
              20, BODY))
body.append(t(88, 640, "coolingDown 이 있어서 같은 위치에서 점이 반복되지 않습니다.", 20, MUTED))
figure("dwell-states", "체류 판정 상태 머신",
       "idle, dwelling, coolingDown 세 상태와 상태를 바꾸는 조건을 화살표로 이은 그림",
       "".join(body))

# --- 14. 별자리 저장 구조 -----------------------------------------------------

body = [heading("노드와 간선으로 별자리 저장하기", "constellations: [Constellation]")]
body.append(rect(56, 168, 988, 300, 24, PANEL, LINE, 2))
body.append(t(88, 214, "constellations", 24, INK, 650, font=MONO))
y = 250
for label, count, color, edge_count in [("[0]", 4, INK, 5), ("[1]", 3, INK, 2)]:
    body.append(rect(88, y, 924, 96, 18, "#0e1524", color, 2))
    body.append(t(116, y + 56, label, 22, color, 650, font=MONO))
    for i in range(count):
        cx = 210 + i * 92
        if i:
            body.append(f'<line x1="{cx-92}" y1="{y+48}" x2="{cx}" y2="{y+48}" '
                        f'stroke="{color}" stroke-width="5" opacity=".6"/>')
    for i in range(count):
        cx = 210 + i * 92
        body.append(f'<circle cx="{cx}" cy="{y+48}" r="18" fill="{color}"/>')
    body.append(t(650, y + 56, f"노드 {count}개 · 간선 {edge_count}개", 20, BODY))
    body.append(t(866, y + 56, "현재" if label == "[1]" else "완료", 18,
                  GREEN if label == "[1]" else MUTED, 650))
    y += 116
body.append(rect(56, 500, 484, 160, 20, "#131b2b", GREEN, 2))
body.append(t(88, 546, "간선이 생기는 곳", 22, GREEN, 650))
body.append(t(88, 588, "현재 Constellation 안의", 19, BODY))
body.append(t(88, 620, "서로 다른 두 노드를 잇습니다.", 19, BODY))
body.append(rect(560, 500, 484, 160, 20, "#131b2b", ORANGE, 2))
body.append(t(592, 546, "선이 생기지 않는 곳", 22, ORANGE, 650))
body.append(t(592, 588, "[0]의 마지막 점과 [1]의 첫 점", 19, BODY))
body.append(t(592, 620, "사이에는 선이 없습니다.", 19, BODY))
figure("constellation-storage", "여러 별자리의 그래프 저장",
       "각 Constellation이 ID가 있는 노드와 중복 없는 간선을 가지며 별자리 사이에는 선이 없음을 보여 주는 그림",
       "".join(body))

# --- 15. 엔티티 트리 ----------------------------------------------------------

body = [heading("RealityKit 엔티티 트리", "ConstellationRenderer.rootEntity")]
body.append(rect(400, 170, 300, 96, 20, PANEL, ACCENT, 3))
body.append(t(550, 214, "rootEntity", 24, ACCENT, 650, "middle", font=MONO))
body.append(t(550, 246, "장면에 추가되는 단 하나의 부모", 17, MUTED, anchor="middle"))
children = [
    ("lineContainer", "흰 확정 선분", INK, 36),
    ("pointContainer", "흰 구 점", INK, 292),
    ("guidanceContainer", "연결 대상·미리보기", INK, 548),
    ("cursor", "흰 검지 커서", INK, 804),
]
for label, note, color, x in children:
    body.append(f'<path d="M550 266 V 320 H {x+118} V 366" fill="none" stroke="{LINE}" stroke-width="3"/>')
    body.append(rect(x, 366, 236, 118, 20, PANEL, color, 2))
    body.append(t(x + 118, 412, label, 17, color, 650, "middle", font=MONO))
    body.append(t(x + 118, 448, note, 16, BODY, anchor="middle"))
body.append(rect(56, 528, 988, 132, 20, "#131b2b", LINE, 2))
body.append(t(88, 572, "컨테이너를 나누면", 22, INK, 650))
body.append(t(88, 612, "초기화할 때 확정 점·선과 연결 안내를 지우고 커서 엔티티는 재사용합니다.", 20, BODY))
body.append(t(88, 644, "목표 점 강조와 미리보기 선은 guidanceContainer 안에서만 켜고 끕니다.", 20, MUTED))
figure("entity-tree", "RealityKit 엔티티 트리",
       "rootEntity 아래에 흰 선, 흰 점, 기존 점 연결 안내 컨테이너와 커서가 자식으로 붙은 구조도",
       "".join(body))

# --- 16. 파일 책임 비교 -------------------------------------------------------

body = [heading("데이터와 화면의 책임 나누기", "ConstellationModel 과 ConstellationRenderer")]
body.append(card(56, 180, 470, 300, "ConstellationModel", [
    "무엇을 저장할지 결정",
    "너무 가까운 점 거절",
    "최대 개수 검사",
    "새 별자리 시작 여부 판단",
    "RealityKit을 import 하지 않음",
], YELLOW))
body.append(card(574, 180, 470, 300, "ConstellationRenderer", [
    "무엇을 보여 줄지 결정",
    "구와 원기둥 mesh 생성",
    "선분의 위치와 회전 계산",
    "커서 크기 갱신",
    "규칙을 스스로 판단하지 않음",
], ACCENT))
body.append(arrow(532, 330, 568, 330))
body.append(t(550, 300, "확정된 점만 전달", 16, MUTED, anchor="middle"))
body.append(rect(56, 512, 988, 148, 20, "#131b2b", GREEN, 2))
body.append(t(88, 556, "이렇게 나누면 좋은 점", 22, GREEN, 650))
body.append(t(88, 598, "모델은 ARKit과 RealityKit 없이 macOS에서 그대로 테스트할 수 있습니다.", 20, BODY))
body.append(t(88, 630, "화면 표현을 바꿔도 별자리 규칙은 손대지 않습니다.", 20, MUTED))
figure("file-responsibilities", "데이터와 화면의 책임 비교",
       "ConstellationModel과 ConstellationRenderer가 각각 맡는 일을 나란히 비교한 표",
       "".join(body))

# --- 17. 입력 처리 순서 -------------------------------------------------------

body = [heading("한 프레임의 입력 처리 순서", "ImmersiveCoordinator.process(anchor:)")]
steps = [
    ("1", "버튼 상태를 먼저 반영", "꺼지는 순간 현재 별자리 마침", ORANGE),
    ("2", "그리기 꺼짐이면 반환", "꺼진 상태에서는 점이 생기지 않음", MUTED),
    ("3", "오른손 검지 위치 계산", "추적 손실이면 후보 입력 취소", ACCENT),
    ("4", "모든 기존 점 후보를 먼저", "스냅 영역이면 일반 점 입력을 멈춤", GREEN),
    ("5", "그 밖의 위치는 점 체류로", "진행률로 커서를 키움", ACCENT),
    ("6", "확정 결과만 모델로", "새 점 또는 기존 노드 간선 추가", YELLOW),
]
y = 136
for number, title, note, color in steps:
    body.append(rect(56, y, 988, 76, 16, PANEL, color, 2))
    body.append(f'<circle cx="106" cy="{y+38}" r="23" fill="{color}"/>')
    body.append(t(106, y + 46, number, 22, "#0b1120", 700, "middle"))
    body.append(t(154, y + 32, title, 21, INK, 650))
    body.append(t(154, y + 61, note, 18, MUTED))
    if number != "6":
        body.append(f'<path d="M550 {y+76} v 4" stroke="{LINE}" stroke-width="3"/>'
                    + head(550, y + 88, 90, LINE, 10))
    y += 88
figure("input-pipeline", "한 프레임의 입력 처리 순서",
       "버튼 상태, 그리기 상태 검사, 검지 위치, 모든 기존 점 연결, 일반 점 체류와 모델 확정 순서도",
       "".join(body))

# --- 18. 실행 대상 선택 -------------------------------------------------------

body = [heading("Apple Vision Pro를 실행 대상으로", "Xcode 도구 막대"), pending_badge()]
body.append(rect(72, 176, 956, 120, 20, "#0b1120", LINE, 2))
body.append(f'<path d="M118 236 l0 -20 l24 20 l-24 20 z" fill="{GREEN}"/>')
body.append(rect(176, 204, 400, 66, 14, "#131b2b", LINE, 2))
body.append(t(200, 244, "HandConstellation", 21, INK, 600, font=MONO))
body.append(rect(600, 204, 396, 66, 14, "#131b2b", FOCUS, 4))
body.append(t(628, 244, "Apple Vision Pro", 21, ACCENT, 650))
body.append(t(886, 244, "내 기기", 18, MUTED))
body.append(rect(72, 330, 460, 330, 22, PANEL, GREEN, 2))
body.append(t(104, 378, "먼저 확인할 것", 24, GREEN, 650))
for i, line in enumerate([
    "Signing & Capabilities 탭에서",
    "Team을 선택했는지",
    "Bundle Identifier가 나만의",
    "고유한 값인지",
    "기기가 Mac과 같은 계정으로",
    "페어링되어 있는지",
]):
    body.append(t(104, 424 + i * 36, line, 19, BODY))
body.append(rect(568, 330, 460, 330, 22, PANEL, ORANGE, 2))
body.append(t(600, 378, "Simulator로는 여기까지", 24, ORANGE, 650))
for i, line in enumerate([
    "창 UI와 몰입형 공간 열기는",
    "Simulator에서도 보입니다.",
    "손 추적은 시작되지 않고",
    "trackingStatus 가",
    "unsupported 가 됩니다.",
]):
    mono = "trackingStatus" in line or "unsupported" in line
    body.append(t(600, 424 + i * 36, line, 19, BODY, font=MONO if mono else FONT))
figure("xcode-run-destination", "Apple Vision Pro 실행 대상 선택",
       "Xcode 도구 막대에서 실행 대상이 Apple Vision Pro로 선택된 상태와 사전 확인 목록",
       "".join(body))

# --- 19. 권한 창 (캡처 대기) --------------------------------------------------

body = [heading("실제 기기의 손 추적 권한 창", "앱을 처음 실행할 때 한 번 나타납니다")]
body.append(rect(W - 246, 46, 190, 40, 20, "none", ORANGE, 2, dash="8 6"))
body.append(t(W - 151, 73, "실제 캡처 대기", 18, ORANGE, 600, "middle"))
body.append(rect(140, 176, 500, 400, 28, "#0e1524", ORANGE, 3, dash="12 9"))
body.append(t(390, 300, "실제 기기 캡처 자리", 26, ORANGE, 650, "middle"))
body.append(t(390, 350, "시스템 권한 창은 흉내 내지 않습니다.", 20, MUTED, anchor="middle"))
body.append(t(390, 388, "Apple Vision Pro에서 직접 캡처한", 20, MUTED, anchor="middle"))
body.append(t(390, 426, "이미지로 교체할 예정입니다.", 20, MUTED, anchor="middle"))
body.append(card(688, 176, 356, 190, "허용하면", [
    "trackingStatus 가 tracking",
    "커서와 점이 동작합니다.",
], GREEN))
body.append(card(688, 386, 356, 190, "허용하지 않으면", [
    "trackingStatus 가 denied",
    "창에 안내가 표시됩니다.",
], ORANGE))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 644, "권한 창에는 Info에 입력한 설명 문장이 그대로 나타납니다.", 20, BODY))
figure("device-permission-prompt", "손 추적 권한 창 안내",
       "실제 기기 캡처를 기다리는 자리 표시와 권한을 허용했을 때와 거부했을 때의 결과 비교",
       "".join(body))

# --- 20. 첫 별자리 -----------------------------------------------------------

def polyline(points, color=INK):
    out = []
    for i in range(1, len(points)):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                   f'stroke-width="9" stroke-linecap="round"/>')
    for x, y in points:
        out.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{INK}" stroke="#ffffff" '
                   f'stroke-width="5"/>')
    return "".join(out)


first = [(170, 470), (280, 300), (420, 400), (520, 250), (640, 360)]
body = [heading("다섯 개의 점으로 만든 첫 별자리", "그리기 켜짐 상태")]
body.append(rect(56, 160, 700, 420, 26, "#070b15", ACCENT, 2, opacity=0.65))
body.append(polyline(first, INK))
for i, (x, y) in enumerate(first):
    body.append(t(x, y - 30, str(i + 1), 20, INK, 700, "middle"))
body.append(f'<circle cx="694" cy="472" r="20" fill="{ORANGE}" opacity=".9"/>')
body.append(t(694, 518, "검지 커서", 18, ORANGE, 600, "middle"))
body.append(card(784, 160, 260, 200, "확인할 것", [
    "점 5개", "선 4개", "별자리 1개",
], GREEN))
body.append(card(784, 380, 260, 200, "만드는 방법", [
    "0.8초 머물러 점 확정",
    "3cm 이상 옮긴 뒤",
    "다음 점을 찍기",
], ACCENT))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 644, "창의 표시가 별자리 1개 · 점 5개 가 되면 성공입니다.", 20, BODY))
figure("device-first-constellation", "다섯 점으로 만든 첫 별자리",
       "번호가 붙은 다섯 개의 흰 점과 이를 잇는 네 개의 흰 선으로 이루어진 첫 별자리",
       "".join(body))

# --- 21. 모든 기존 점 연결 피드백 -------------------------------------------

body = [heading("어느 기존 점으로든 다시 연결", "새 점 대신 저장된 목표 노드를 선택합니다")]
panels = [
    (56, "1. 목표 선택", "가까운 기존 점을 고정"),
    (392, "2. 목표에서 머무르기", "미리보기 선과 진행률"),
    (728, "3. 연결 완료", "점 수 유지 · 선만 추가"),
]
for x, title, note in panels:
    body.append(rect(x, 158, 316, 420, 24, "#070b15", LINE, 2, opacity=0.72))
    body.append(t(x + 24, 202, title, 22, INK, 650))
    body.append(t(x + 24, 548, note, 18, MUTED))

panel_points = [(118, 452), (214, 278), (318, 448)]
for panel_index, panel_x in enumerate([0, 336, 672]):
    pts = [(x + panel_x, y) for x, y in panel_points]
    body.append(polyline(pts[:3], INK))
    if panel_index == 2:
        (x1, y1), (x2, y2) = pts[2], pts[0]
        body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')
    target_x, target_y = pts[0]
    body.append(f'<circle cx="{target_x}" cy="{target_y}" r="31" fill="none" '
                f'stroke="{INK}" stroke-width="6" opacity=".65"/>')
    if panel_index == 1:
        last_x, last_y = pts[2]
        body.append(f'<line x1="{last_x}" y1="{last_y}" x2="{target_x}" y2="{target_y}" '
                    f'stroke="{INK}" stroke-width="6" stroke-dasharray="14 10" opacity=".45"/>')
        body.append(f'<circle cx="{target_x+16}" cy="{target_y-12}" r="16" fill="{INK}" opacity=".72"/>')
        body.append(t(target_x + 52, target_y - 34, "검지 커서", 16, INK, 600))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", GREEN, 2))
body.append(t(88, 644, "선의 끝은 손가락 좌표가 아니라 저장된 목표 점 좌표이므로 정확히 만납니다.", 20, BODY))
figure("closure-snap-feedback", "모든 기존 점으로 다시 연결",
       "여러 기존 점 중 목표 선택, dwell 미리보기, 점을 추가하지 않는 연결 완료 상태",
       "".join(body))

# --- 22. 여러 기존 점을 잇는 그래프 -----------------------------------------

graph_points = [(170, 470), (350, 230), (590, 300), (640, 500)]
graph_edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
body = [heading("기존 점을 다시 이은 첫 별자리", "어느 기존 점에서든 0.8초 머물러 선 추가")]
body.append(rect(56, 160, 700, 420, 26, "#070b15", ACCENT, 2, opacity=0.65))
for start, end in graph_edges:
    x1, y1 = graph_points[start]
    x2, y2 = graph_points[end]
    body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{INK}" stroke-width="7" stroke-linecap="round" opacity=".92"/>')
for index, (x, y) in enumerate(graph_points):
    body.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{INK}" stroke="#ffffff" stroke-width="4"/>')
    body.append(t(x, y - 32, str(index + 1), 20, INK, 700, "middle"))
body.append(f'<circle cx="590" cy="300" r="34" fill="none" stroke="{INK}" stroke-width="6" opacity=".5"/>')
body.append(card(784, 160, 260, 200, "완료 상태", [
    "별자리 1개", "점 4개", "선 5개",
], GREEN))
body.append(card(784, 380, 260, 200, "제어창 안내", [
    "기존 점에 연결했어요", "이미 있는 선은", "중복 생성하지 않음",
], ACCENT))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 644, "기존 점을 복제하지 않고 간선만 추가하므로 점 개수는 그대로 유지됩니다.", 20, BODY))
figure("device-closed-triangle", "모든 기존 점 연결 결과",
       "흰 점 네 개와 흰 선 다섯 개로 만든 그래프, 기존 점 연결 완료 안내",
       "".join(body))

# --- 23. 두 번째 별자리 ------------------------------------------------------

body = [heading("분리된 두 번째 별자리", "그리기를 끄고 다시 켠 뒤")]
body.append(rect(56, 160, 988, 420, 26, "#070b15", ACCENT, 2, opacity=0.65))
body.append(polyline([(120, 470), (270, 250), (480, 470), (120, 470)], INK))
body.append(polyline([(700, 470), (800, 320), (910, 420), (985, 272)], INK))
body.append(f'<circle cx="640" cy="418" r="38" fill="none" stroke="{ORANGE}" stroke-width="5"/>')
body.append(f'<path d="M616 394 l48 48" stroke="{ORANGE}" stroke-width="6" stroke-linecap="round"/>')
body.append(t(640, 512, "여기에 선이 없어야 합니다", 20, ORANGE, 650, "middle"))
body.append(t(300, 214, "첫 번째 별자리", 21, YELLOW, 650, "middle"))
body.append(t(846, 214, "두 번째 별자리", 21, YELLOW, 650, "middle"))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", GREEN, 2))
body.append(t(88, 644, "창의 표시가 별자리 2개 · 점 7개 가 되면 별자리 분리가 올바르게 동작한 것입니다.",
              20, BODY))
figure("device-second-constellation", "분리된 두 번째 별자리",
       "첫 번째 별자리와 두 번째 별자리 사이에 선이 없음을 강조 표시로 나타낸 화면",
       "".join(body))


def main() -> None:
    for name, content in FIGURES.items():
        svg_path = OUT / f"{name}.svg"
        svg_path.write_text(content, encoding="utf-8")
        png_path = OUT / f"{name}.png"
        direct = subprocess.run(
            ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
            capture_output=True,
        )
        if direct.returncode != 0:
            with tempfile.TemporaryDirectory(prefix="hand-constellation-svg-") as temporary_directory:
                temporary_path = Path(temporary_directory)
                square_svg = temporary_path / f"{name}.svg"
                square_svg.write_text(
                    content.replace(
                        'height="720" viewBox="0 0 1100 720"',
                        'height="1100" viewBox="0 0 1100 1100"',
                        1,
                    ),
                    encoding="utf-8",
                )
                subprocess.run(
                    ["qlmanage", "-t", "-s", "1100", "-o", str(temporary_path), str(square_svg)],
                    check=True,
                    capture_output=True,
                )
                square_png = temporary_path / f"{name}.svg.png"
                subprocess.run(
                    [
                        "sips", "-c", "720", "1100", "--cropOffset", "0", "0",
                        str(square_png), "--out", str(png_path),
                    ],
                    check=True,
                    capture_output=True,
                )
    print(f"wrote {len(FIGURES)} figures as SVG and PNG")


if __name__ == "__main__":
    main()
