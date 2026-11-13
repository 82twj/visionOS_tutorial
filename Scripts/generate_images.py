#!/usr/bin/env python3
"""Generates the DocC tutorial illustrations as SVG and rasterizes them to PNG.

Every drawing uses the same dark spatial palette as the existing hero art so
that a page mixing old and new figures still reads as one set.

    python3 Scripts/generate_images.py                      # every figure
    python3 Scripts/generate_images.py --only prerequisites,interaction-overview
    python3 Scripts/generate_images.py --list               # figure names

Animated figures (GIF) are drawn frame by frame as SVG, rasterized with sips
and joined with ffmpeg (palettegen + paletteuse).
"""

import argparse
import math
import shutil
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


def svg(title, desc, body, w=W, h=H, size=None):
    """`size` renders the same w×h drawing at another pixel size (used for GIF frames)."""
    out_w, out_h = size or (w, h)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{out_w}" height="{out_h}" '
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

body = [heading("버튼으로 공유 상태 바꾸기", "개념도 · 제어창과 몰입형 공간이 같은 AppModel을 읽습니다")]
body.append(card(56, 170, 450, 280, "그리기 꺼짐", [
    "drawingState = .disabled", "손을 움직여도 새 점을 만들지 않습니다.", "기존 별자리는 화면에 남습니다.",
], MUTED))
body.append(card(594, 170, 450, 280, "그리기 켜짐", [
    "drawingState = .enabled", "검지를 0.8초 머물러 점을 만듭니다.", "기존 점에 머물러 선을 연결합니다.",
], GREEN))
body.append(arrow(300, 500, 800, 500, GREEN))
body.append(t(550, 484, "제어창에서 ‘그리기 켜기’ 버튼", 23, INK, 600, "middle"))
body.append(arrow(800, 570, 300, 570, MUTED))
body.append(t(550, 609, "제어창에서 ‘그리기 끄기’ 버튼", 23, INK, 600, "middle"))
body.append(t(550, 671, "꺼진 뒤 다시 켜면 다음 첫 점은 새 별자리를 시작합니다.", 21, BODY, 400, "middle"))
figure("drawing-toggle", "버튼으로 그리기 상태 전환", "그리기 켜기와 끄기 버튼이 공유 AppModel의 상태를 변경하는 개념도", "".join(body))

body = [heading("이 과정을 시작하기 전에", "필요한 사전 지식과 확인 환경")]
body.append(card(56, 160, 320, 300, "이미 알고 있어야 함", [
    "Swift 문법과 옵셔널", "struct와 class의 차이", "SwiftUI View와 상태", "Xcode에서 빌드·실행하기",
], GREEN))
body.append(card(392, 160, 320, 300, "이 과정에서 설명함", [
    "ARKit 손 추적", "RealityKit 엔티티", "simd 좌표 변환", "머무르기 판정 상태 머신",
], ACCENT))
body.append(card(728, 160, 316, 300, "확인 환경", [
    "Xcode 16 이상", "visionOS 2.0 이상 SDK", "Simulator: Chapter 1–4", "Vision Pro: Chapter 5",
], YELLOW))
body.append(rect(56, 500, 988, 160, 22, "#131b2b", ORANGE, 2))
body.append(t(88, 552, "Simulator에서 확인할 수 없는 것", 24, ORANGE, 650))
body.append(t(88, 594, "ARKit 손 추적은 Apple Vision Pro에서만 동작합니다. Chapter 4까지는 Simulator에서", 20, BODY))
body.append(t(88, 626, "제어창과 몰입형 공간이 열리는지 확인하고, 점과 선은 Chapter 5에서 Vision Pro로 그려 봅니다.", 20, BODY))
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
    ("머무르기 판정", GREEN, [
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
       "머무르기 판정과 점·선 두 묶음으로 나눈 설정값과 미터 단위 환산 표",
       "".join(body))

# --- 12. 체류 상태 머신 -------------------------------------------------------

body = [heading("머무르기 판정 상태 머신", "DwellDetector.State")]
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
body.append(t(88, 606, "점은 dwelling에서 coolingDown으로 넘어가는 그 한 프레임에만 찍힙니다.",
              20, BODY))
body.append(t(88, 640, "coolingDown 덕분에 같은 자리에서 점이 여러 번 찍히지 않습니다.", 20, MUTED))
figure("dwell-states", "머무르기 판정 상태 머신",
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
    if edge_count > count - 1:  # 기존 점으로 다시 이은 선 3→0, 0→2
        body.append(f'<path d="M210 {y+48} Q348 {y+120} 486 {y+48}" fill="none" '
                    f'stroke="{color}" stroke-width="5" opacity=".6"/>')
        body.append(f'<path d="M210 {y+48} Q302 {y-24} 394 {y+48}" fill="none" '
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
    ("lineContainer", "흰 선", INK, 36),
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
body.append(t(88, 612, "초기화할 때 찍은 점·선과 연결 안내만 지우고 커서 엔티티는 다시 씁니다.", 20, BODY))
body.append(t(88, 644, "목표 점 강조와 미리보기 선은 guidanceContainer 안에서만 켜고 끕니다.", 20, MUTED))
figure("entity-tree", "RealityKit 엔티티 트리",
       "rootEntity 아래에 흰 선, 흰 점, 기존 점 연결 안내 컨테이너와 커서가 자식으로 붙은 구조도",
       "".join(body))

# --- 17. 입력 처리 순서 -------------------------------------------------------

body = [heading("한 프레임의 입력 처리 순서", "ImmersiveCoordinator.process(anchor:)")]
steps = [
    ("1", "버튼 상태를 먼저 반영", "꺼지는 순간 현재 별자리 마침", ORANGE),
    ("2", "그리기 꺼짐이면 반환", "꺼진 상태에서는 점이 생기지 않음", MUTED),
    ("3", "오른손 검지 위치 계산", "추적을 놓치면 진행 중인 머무르기 취소", ACCENT),
    ("4", "기존 점 연결을 먼저 확인", "기존 점 3cm 안이면 새 점 머무르기를 멈춤", GREEN),
    ("5", "그 밖의 위치는 새 점 머무르기로", "진행 정도만큼 커서를 키움", ACCENT),
    ("6", "머무르기가 끝나면 모델에 반영", "새 점과 선, 또는 기존 점으로 선만 추가", YELLOW),
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
       "버튼 상태, 그리기 상태 검사, 검지 위치, 기존 점 연결, 새 점 머무르기, 모델 반영 순서도",
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
first_graph = [(110, 452), (245, 260), (425, 316), (462, 476)]
for start, end in graph_edges:
    (x1, y1), (x2, y2) = first_graph[start], first_graph[end]
    body.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{INK}" stroke-width="7" stroke-linecap="round" opacity=".92"/>')
for x, y in first_graph:
    body.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{INK}" stroke="#ffffff" stroke-width="4"/>')
body.append(polyline([(720, 470), (840, 290), (980, 440), (720, 470)], INK))
body.append(f'<circle cx="640" cy="418" r="38" fill="none" stroke="{ORANGE}" stroke-width="5"/>')
body.append(f'<path d="M616 394 l48 48" stroke="{ORANGE}" stroke-width="6" stroke-linecap="round"/>')
body.append(t(640, 512, "여기에 선이 없어야 합니다", 20, ORANGE, 650, "middle"))
body.append(t(286, 214, "첫 번째 별자리 · 점 4개 · 선 5개", 21, YELLOW, 650, "middle"))
body.append(t(850, 214, "두 번째 별자리 · 점 3개 · 선 3개", 21, YELLOW, 650, "middle"))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", GREEN, 2))
body.append(t(88, 644, "창에 별자리 2개 · 점 7개 · 선 8개가 보이면 두 별자리가 제대로 나뉜 것입니다.",
              20, BODY))
figure("device-second-constellation", "분리된 두 번째 별자리",
       "점 4개·선 5개인 첫 번째 별자리와 점 3개·선 3개인 두 번째 별자리 사이에 선이 없음을 강조한 개념도",
       "".join(body))




# --- 24. 완성 동작: 커서, 머무르기, 다음 점, 기존 점 연결 ------------------------
#
# interaction-overview.gif 와 세 장의 정지 화면이 같은 장면 함수를 씁니다.
# 1cm를 22px로 그립니다. 점은 렌더러처럼 흰 구, 선은 흰 원기둥, 커서는 반투명
# 흰 구이고, 기존 점 강조는 더 큰 반투명 흰 구, 미리보기 선은 흐린 선입니다.

SCENE = (56, 148, 988, 432)
PA, PB, PC = (290, 430), (530, 262), (790, 392)
CM = 22
SNAP_R = 3 * CM
PROGRESS = "#8edfff"
SKIN, SKIN_LIGHT, SKIN_KNUCKLE = "#e9a98f", "#f4b99f", "#eeb39a"
LETTERS = {"A": (208, 402), "B": (530, 184), "C": (872, 404)}
# 3cm 표시는 이미 있는 선과 겹치지 않는 쪽에 둡니다.
REARM_LABEL_SIDE = {PA: "lower-left", PB: "upper-right", PC: "lower-left"}

START = (170, 520)
LOOP_SECONDS = 8.0
GIF_FPS = 12
# (시작, 끝, 출발점, 제어점, 도착점): 검지 끝이 움직이는 구간
MOVES = [
    (0.00, 0.70, START, (200, 440), PA),
    (1.75, 2.45, PA, (390, 318), PB),
    (3.45, 4.10, PB, (680, 300), PC),
    (5.10, 5.80, PC, (560, 480), PA),
    (7.60, 8.00, PA, (220, 500), START),
]
# (시작, 끝, 커서 모드): 0.8초 머무르기
DWELLS = [
    (0.70, 1.50, "point"),
    (2.45, 3.25, "point"),
    (4.10, 4.90, "point"),
    (5.80, 6.60, "connection"),
]
PLACED = {"A": 1.50, "B": 3.25, "C": 4.90}
EDGES = [("A", "B", 3.25), ("B", "C", 4.90), ("C", "A", 6.60)]
CONNECTED_AT = 6.60
FADE_FROM = 7.60


def text_width(s, size):
    """Rough rendered width; Korean glyphs are about one em, Latin about half."""
    width = 0.0
    for ch in s:
        if ord(ch) >= 0x1100:
            width += 0.94
        elif ch == " ":
            width += 0.3
        else:
            width += 0.56
    return width * size


def pill(x, y, label, color=INK, size=19, anchor="start", stroke=LINE):
    """A readable label on a dark rounded plate. (x, y) is the text baseline start."""
    w = text_width(label, size) + 28
    left = x if anchor == "start" else x - w
    return (
        rect(left, y - size - 9, w, size + 22, (size + 22) / 2, "#131b2b", stroke, 2, opacity=0.94)
        + t(left + 14, y, label, size, color, 600)
    )


def pill_end(x, label, size=19):
    return x + text_width(label, size) + 28


def leader(x1, y1, x2, y2):
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED}" stroke-width="2"/>'
        f'<circle cx="{x2}" cy="{y2}" r="4" fill="{MUTED}"/>'
    )


def hand(x, y):
    """A right hand seen from behind with the index finger raised; (x, y) is the fingertip."""
    return (
        f'<g transform="translate({x:.1f} {y:.1f}) rotate(-14) scale(0.9)">'
        f'<g transform="translate(-26 170) rotate(-38)">'
        f'<rect x="-14" y="-84" width="28" height="94" rx="14" fill="{SKIN}"/></g>'
        f'<rect x="-36" y="98" width="138" height="170" rx="48" fill="{SKIN}"/>'
        f'<rect x="14" y="82" width="30" height="62" rx="15" fill="{SKIN_KNUCKLE}"/>'
        f'<rect x="45" y="92" width="28" height="56" rx="14" fill="{SKIN_KNUCKLE}"/>'
        f'<rect x="72" y="106" width="25" height="48" rx="12.5" fill="{SKIN_KNUCKLE}"/>'
        f'<rect x="-15" y="-8" width="30" height="134" rx="15" fill="{SKIN_LIGHT}"/>'
        f'</g>'
    )


def progress_arc(cx, cy, r, p):
    if p >= 0.999:
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{PROGRESS}" '
                f'stroke-width="6"/>')
    a = math.radians(-90 + 360 * p)
    ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
    large = 1 if p > 0.5 else 0
    return (f'<path d="M{cx:.1f} {cy - r:.1f} A{r} {r} 0 {large} 1 {ex:.1f} {ey:.1f}" fill="none" '
            f'stroke="{PROGRESS}" stroke-width="6" stroke-linecap="round"/>')


def cursor(x, y, progress=0.0, mode="point"):
    """The fingertip cursor grows while dwelling; connection mode is fully white."""
    if mode == "point":
        r, fill_opacity, ring = 11 + 11 * progress, 0.72, 36
    else:
        r, fill_opacity, ring = 14 + 12 * progress, 1, 54
    out = [
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 9:.1f}" fill="#ffffff" opacity=".10"/>',
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" opacity="{fill_opacity}"/>',
    ]
    if progress > 0:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{ring}" fill="none" stroke="#ffffff" '
                   f'stroke-width="6" opacity=".14"/>')
        out.append(progress_arc(x, y, ring, progress))
        label = f"{0.8 * progress:.1f}초"
        if mode == "point":
            out.append(t(x + ring * 0.74 + 10, y - ring * 0.74 - 2, label, 18, PROGRESS, 650))
        else:
            out.append(t(x - ring - 10, y + 6, label, 18, PROGRESS, 650, "end"))
    return "".join(out)


def star(x, y, opacity=1.0):
    return (f'<circle cx="{x}" cy="{y}" r="16" fill="{INK}" stroke="#ffffff" stroke-width="5" '
            f'opacity="{opacity:.2f}"/>')


def segment(p, q, opacity=0.92):
    return (f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="#ffffff" '
            f'stroke-width="9" stroke-linecap="round" opacity="{opacity:.2f}"/>')


def preview_line(p, q, opacity=0.45):
    return (f'<line x1="{p[0]}" y1="{p[1]}" x2="{q[0]}" y2="{q[1]}" stroke="#ffffff" '
            f'stroke-width="5" stroke-dasharray="14 10" stroke-linecap="round" '
            f'opacity="{opacity:.2f}"/>')


def target_highlight(x, y, progress, opacity=1.0):
    r = 26 * (1 + 0.6 * progress)
    return (f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="#ffffff" opacity="{0.2 * opacity:.2f}"/>'
            f'<circle cx="{x}" cy="{y}" r="{r:.1f}" fill="none" stroke="#ffffff" stroke-width="2" '
            f'opacity="{0.5 * opacity:.2f}"/>')


def pop(x, y, k):
    return (f'<circle cx="{x}" cy="{y}" r="{20 + 34 * k:.1f}" fill="none" stroke="#ffffff" '
            f'stroke-width="4" opacity="{0.7 * (1 - k):.2f}"/>')


def rearm_circle(center, opacity):
    x, y = center
    d = SNAP_R * 0.72
    if REARM_LABEL_SIDE.get(center, "lower-left") == "upper-right":
        label = t(x + d + 6, y - d - 6, "3cm", 18, ACCENT, 650)
    else:
        label = t(x - d - 6, y + d + 22, "3cm", 18, ACCENT, 650, "end")
    return (f'<g opacity="{opacity:.2f}"><circle cx="{x}" cy="{y}" r="{SNAP_R}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="3" stroke-dasharray="6 8"/>' + label + '</g>')


def counter_pill(points, lines, point_color=INK, line_color=INK):
    return (
        rect(800, 616, 224, 52, 26, "#0e1524", LINE, 2)
        + t(900, 650, f"점 {points}개", 21, point_color, 650, "end")
        + t(912, 649, "·", 21, MUTED, 400, "middle")
        + t(924, 650, f"선 {lines}개", 21, line_color, 650)
    )


def hud(step, caption, points, lines, point_color=INK, line_color=INK):
    return (
        rect(56, 604, 988, 76, 18, "#131b2b", LINE, 2)
        + f'<circle cx="100" cy="642" r="20" fill="{ACCENT}"/>'
        + t(100, 649, str(step), 20, "#0b1120", 700, "middle")
        + t(136, 650, caption, 22, INK, 600)
        + counter_pill(points, lines, point_color, line_color)
    )


def _ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _bezier(p0, p1, p2, u):
    a, b, c = (1 - u) ** 2, 2 * (1 - u) * u, u * u
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def fingertip_at(time):
    position = START
    for t0, t1, p0, p1, p2 in MOVES:
        if t0 <= time <= t1:
            return _bezier(p0, p1, p2, _ease((time - t0) / (t1 - t0)))
        if time > t1:
            position = p2
    return position


def dwell_at(time):
    for t0, t1, mode in DWELLS:
        if t0 <= time < t1:
            return (time - t0) / (t1 - t0), mode
    return 0.0, None


def caption_at(time):
    if time < 0.70:
        return 1, "검지 끝을 따라 커서가 움직입니다"
    if time < 1.75:
        return 2, "한곳에 0.8초 머무르면 점이 찍힙니다"
    if time < 5.10:
        return 3, "3cm 이상 옮긴 뒤 다시 머무르면 점과 선"
    if time < CONNECTED_AT:
        return 4, "기존 점에 머무르면 강조 표시와 미리보기 선"
    return 4, "기존 점에 머무르면 선만 추가 · 점 수는 그대로"


def interaction_scene(time, pops=True, rearm=True, extra="", hud_override=None):
    """Everything below the heading at one moment of the loop."""
    sx, sy, sw, sh = SCENE
    fade = 1.0 if time < FADE_FROM else max(0.0, 1 - (time - FADE_FROM) / 0.35)
    tip = fingertip_at(time)
    progress, mode = dwell_at(time)
    points = {k: v for k, v in {"A": PA, "B": PB, "C": PC}.items() if time >= PLACED[k]}

    near_a = math.dist(tip, PA) <= SNAP_R
    connecting = len(points) == 3 and near_a and time >= 5.10
    if connecting:
        mode = "connection"

    out = [
        '<defs><clipPath id="scene"><rect x="56" y="148" width="988" height="432" rx="26"/>'
        '</clipPath></defs>',
        rect(sx, sy, sw, sh, 26, "#070b15", ACCENT, 2, opacity=0.65),
        f'<g clip-path="url(#scene)">{hand(*tip)}</g>',
    ]
    content = []
    for a, b, at in EDGES:
        if time >= at:
            content.append(segment({"A": PA, "B": PB, "C": PC}[a], {"A": PA, "B": PB, "C": PC}[b]))
    if connecting and time < CONNECTED_AT:
        content.append(preview_line(PC, PA))
    if connecting:
        highlight_progress = 1.0 if time >= CONNECTED_AT else (progress if mode == "connection" else 0)
        content.append(target_highlight(*PA, highlight_progress))
    for name, (x, y) in points.items():
        content.append(star(x, y))
        lx, ly = LETTERS[name]
        content.append(t(lx, ly, name, 19, MUTED, 700, "middle"))
    if rearm:
        for name, follow_until in (("A", 2.45), ("B", 4.10), ("C", 5.80)):
            if PLACED[name] <= time < follow_until:
                center = {"A": PA, "B": PB, "C": PC}[name]
                d = math.dist(tip, center)
                opacity = max(0.0, min(1.0, (1.5 * SNAP_R - d) / (0.5 * SNAP_R)))
                if opacity > 0:
                    content.append(rearm_circle(center, opacity))
    if pops:
        for name, at in PLACED.items():
            if 0 <= time - at < 0.35:
                content.append(pop(*{"A": PA, "B": PB, "C": PC}[name], (time - at) / 0.35))
        if 0 <= time - CONNECTED_AT < 0.35:
            content.append(pop(*PA, (time - CONNECTED_AT) / 0.35))
    out.append(f'<g opacity="{fade:.2f}">{"".join(content)}</g>')
    out.append(cursor(*tip, progress if mode else 0.0, mode or "point"))
    out.append(extra)

    if hud_override is not None:
        out.append(hud_override)
    else:
        step, caption = caption_at(time)
        n_points = len(points)
        n_lines = sum(1 for _, _, at in EDGES if time >= at)
        point_color = line_color = INK
        if time >= CONNECTED_AT:
            point_color, line_color = GREEN, YELLOW  # 점은 그대로, 선만 +1
        else:
            for at, changed in ((1.50, "point"), (3.25, "both"), (4.90, "both")):
                if 0 <= time - at < 0.9:
                    point_color = YELLOW
                    line_color = YELLOW if changed == "both" else INK
        out.append(hud(step, caption, n_points, n_lines, point_color, line_color))
    return "".join(out)


OVERVIEW_TITLE = "검지로 별자리 그리기"
OVERVIEW_SUB = "개념도 · 머무르기로 점을 찍고, 기존 점에 다시 머물러 선을 잇습니다"


def interaction_frames():
    frames = []
    count = int(round(LOOP_SECONDS * GIF_FPS))
    for i in range(count):
        time = i / GIF_FPS
        body = heading(OVERVIEW_TITLE, OVERVIEW_SUB) + interaction_scene(time)
        frames.append(svg("검지로 별자리 그리기",
                          "검지 커서로 점 A, B, C를 찍고 기존 점 A에 머물러 선만 추가하는 반복 애니메이션",
                          body, size=(880, 576)))
    return frames, GIF_FPS


ANIMATIONS = {"interaction-overview": interaction_frames}

# 정지 화면 1: 머무르기
extra = (
    leader(228, 480, 272, 446) + pill(96, 492, "검지 끝이 커서", INK, 19)
    + leader(250, 352, 263, 402) + pill(96, 338, "진행 표시가 다 차면 흰 점", INK, 19)
)
body = [heading("검지를 멈추고 0.8초 머무르기",
                "개념도 · 머무르는 동안 커서가 커지고, 0.8초가 차면 그 자리에 흰 점이 찍힙니다")]
body.append(interaction_scene(1.30, pops=False, extra=extra,
                              hud_override=hud(2, "1.5cm 안에서 0.8초 머무르면 점이 찍힙니다", 0, 0)))
figure("interaction-dwell", "검지를 멈추고 0.8초 머무르기",
       "검지 끝 커서가 한곳에 머무르는 동안 커지고 둘레의 진행 표시가 차오르는 개념도",
       "".join(body))

# 정지 화면 2: 3cm 이동 후 다음 점
trail = (f'<path d="M{PA[0] + 30} {PA[1] + 10} Q470 420 {PB[0] - 6} {PB[1] + 44}" fill="none" '
         f'stroke="{MUTED}" stroke-width="3" stroke-dasharray="3 9" stroke-linecap="round"/>'
         + head(PB[0] - 6, PB[1] + 44, -78, MUTED, 13))
extra = (
    trail + rearm_circle(PA, 1.0)
    + pill(372, 522, "3cm 이상 옮기기", INK, 19)
    + leader(pill_end(96, "다시 0.8초 머무르면 점 B와 선"), 218, 508, 252)
    + pill(96, 226, "다시 0.8초 머무르면 점 B와 선", INK, 19)
)
body = [heading("3cm 이상 옮긴 뒤 다시 머무르기",
                "개념도 · 직전 점에서 3cm 밖으로 나간 뒤 머물러야 다음 점과 선이 생깁니다")]
body.append(interaction_scene(3.40, pops=False, rearm=False, extra=extra,
                              hud_override=hud(3, "점 B가 찍히고 A–B 선이 생깁니다", 2, 1,
                                               YELLOW, YELLOW)))
figure("interaction-next-point", "3cm 이상 옮긴 뒤 다시 머무르기",
       "첫 점 A 둘레의 3cm 점선 원 밖으로 검지를 옮겨 점 B를 찍고 A와 B를 잇는 흰 선이 생긴 개념도",
       "".join(body))

# 정지 화면 3: 기존 점 연결
extra = (
    leader(240, 486, 266, 455) + pill(80, 500, "기존 점 A 강조", INK, 19)
    + leader(548, 482, 548, 416) + pill(470, 510, "미리보기 선 C–A", INK, 19)
)
body = [heading("기존 점에 머무르면 선만 추가",
                "개념도 · 3cm 안의 기존 점을 고르면 새 점을 만들지 않고 선 하나만 늘어납니다")]
body.append(interaction_scene(6.15, pops=False, extra=extra,
                              hud_override=hud(4, "머무르기가 끝나면 C–A 선만 추가됩니다", 3, 2)))
figure("interaction-connect", "기존 점에 머무르면 선만 추가",
       "기존 점 A가 반투명 흰 구로 강조되고 C에서 A로 흐린 미리보기 선이 보이는 개념도",
       "".join(body))


# --- 25. 검지 끝 월드 좌표 숫자 예시 ---------------------------------------------

CELL_W, CELL_H = 66, 34
MAT_W = 4 * CELL_W + 28
TOPDOWN_PX_PER_CM = 14


def num(v):
    if v == 0:
        return "0"
    if abs(v) == 1:
        return "−1" if v < 0 else "1"
    return ("−" if v < 0 else "") + f"{abs(v):.2f}"


def matmul(a, b):
    return [[round(sum(a[r][k] * b[k][c] for k in range(4)), 6) for c in range(4)] for r in range(4)]


def transform(rotation, translation):
    rows = [list(rotation[r]) + [translation[r]] for r in range(3)]
    return rows + [[0, 0, 0, 1]]


def matrix(x, y, m, title, note, block_label, block_color):
    out = [t(x + MAT_W / 2, y, title, 17, INK, 650, "middle", font=MONO),
           t(x + MAT_W / 2, y + 25, note, 17, MUTED, anchor="middle")]
    top = y + 42
    h = 4 * CELL_H + 12
    gx = x + 14
    out.append(rect(gx + 3, top + 4, 3 * CELL_W - 6, 3 * CELL_H + 4, 10, block_color, None,
                    opacity=0.16))
    out.append(rect(gx + 3 * CELL_W + 4, top + 2, CELL_W - 8, h - 4, 10, YELLOW, None, opacity=0.14))
    out.append(rect(gx + 3 * CELL_W + 4, top + 2, CELL_W - 8, h - 4, 10, "none", YELLOW, 2))
    out.append(f'<path d="M{x + 12} {top} h-8 v{h} h8" fill="none" stroke="{BODY}" stroke-width="2.5"/>')
    out.append(f'<path d="M{x + MAT_W - 12} {top} h8 v{h} h-8" fill="none" stroke="{BODY}" '
               f'stroke-width="2.5"/>')
    for r in range(4):
        for c in range(4):
            v = m[r][c]
            position = c == 3 and r < 3
            color = YELLOW if position else (MUTED if r == 3 or v == 0 else BODY)
            out.append(t(gx + c * CELL_W + CELL_W / 2, top + 6 + r * CELL_H + 23, num(v), 18, color,
                         650 if position else 400, "middle", font=MONO))
    out.append(t(gx + 1.5 * CELL_W, top + h + 24, block_label, 15, block_color, 650, "middle"))
    out.append(t(gx + 3.5 * CELL_W, top + h + 24, "columns.3", 15, YELLOW, 650, "middle", font=MONO))
    return "".join(out)


def matrix_row(a, j, block_a, block_a_color):
    p = matmul(a, j)
    xs = (56, 392, 728)
    out = [
        matrix(xs[0], 162, a, "originFromAnchorTransform", "손 앵커 → 월드", block_a, block_a_color),
        t(370, 296, "×", 40, INK, 700, "middle"),
        matrix(xs[1], 162, j, "anchorFromJointTransform", "검지 끝 → 손 앵커", "회전 없음", MUTED),
        t(706, 296, "=", 40, INK, 700, "middle"),
        matrix(xs[2], 162, p, "originFromJoint", "검지 끝 → 월드", block_a, block_a_color),
    ]
    return "".join(out), p


def hand_top(x, y, angle=0, ghost=False):
    """A right hand seen from above, pointing with the index finger; (x, y) is the wrist anchor.

    The hand is drawn along its own axis and turned so that the index fingertip lands on
    OFFSET (x, z) when `angle` is 0; `angle` then adds the hand's rotation on screen.
    """
    s = TOPDOWN_PX_PER_CM
    reach = math.hypot(OFFSET[0], OFFSET[2]) * 100
    lean = math.degrees(math.atan2(OFFSET[0], -OFFSET[2]))
    shapes = [  # x, y, w, h, rx in cm; the finger points to −y
        (-1.7, -0.8, 3.4, 5.6, 1.5),                        # 손목
        (-2.3, -6.2, 4.8, 6.0, 2.2),                        # 손등과 접은 손가락
        (-3.3, -5.0, 1.7, 3.6, 0.85),                       # 엄지
        (-0.75, -reach - 0.75, 1.5, reach - 4.6, 0.75),     # 펴진 검지
    ]
    knuckles = [(0.9, -6.0), (1.9, -5.6)]
    if ghost:
        parts = [rect(sx * s, sy * s, w * s, h * s, r * s, "none", MUTED, 2, dash="6 6")
                 for sx, sy, w, h, r in shapes]
        return (f'<g transform="translate({x} {y}) rotate({angle + lean:.2f})" opacity=".8">'
                + "".join(parts) + "</g>")
    parts = [rect(sx * s, sy * s, w * s, h * s, r * s, SKIN_LIGHT) for sx, sy, w, h, r in shapes]
    parts += [f'<circle cx="{kx * s:.1f}" cy="{ky * s:.1f}" r="{0.75 * s:.1f}" fill="{SKIN_KNUCKLE}"/>'
              for kx, ky in knuckles]
    return (f'<g transform="translate({x} {y}) rotate({angle + lean:.2f})" opacity=".82">'
            + "".join(parts) + "</g>")


def topdown_panel(anchor, inner):
    """The bottom-left panel: the hand seen from above with world axes."""
    out = ['<defs><clipPath id="topdown"><rect x="56" y="400" width="470" height="276" rx="22"/>'
           '</clipPath></defs>',
           rect(56, 400, 470, 276, 22, "#131b2b", LINE, 2),
           t(80, 436, "위에서 본 모습", 21, INK, 650),
           t(80, 462, "높이 y는 생략 · 1cm를 14px로", 16, MUTED),
           f'<circle cx="352" cy="430" r="7" fill="{ACCENT}"/>',
           t(366, 436, "손 앵커", 16, BODY),
           f'<circle cx="440" cy="430" r="7" fill="{YELLOW}"/>',
           t(454, 436, "검지 끝", 16, BODY),
           f'<g clip-path="url(#topdown)">{inner}</g>',
           arrow(452, 650, 498, 650, MUTED, 3), t(504, 656, "+x", 16, MUTED, 600),
           arrow(452, 650, 452, 604, MUTED, 3), t(452, 594, "−z 앞", 16, MUTED, 600, "middle")]
    ax, ay = anchor
    out.append(f'<circle cx="{ax}" cy="{ay}" r="8" fill="{ACCENT}" stroke="#d8f5ff" stroke-width="3"/>')
    return "".join(out)


def tip_dot(x, y, color=YELLOW, stroke="#fff1a8"):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{color}" stroke="{stroke}" stroke-width="3"/>'


IDENTITY = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
# y축 +90°: 오른손 법칙(엄지를 +y로)으로 돌리면 위에서 볼 때 시계 반대 방향입니다.
# R·(1,0,0) = (0,0,−1), R·(0,0,−1) = (−1,0,0): 손의 앞(−z)이 월드의 왼쪽(−x)을 향합니다.
ROT_Y_90 = ((0, 0, 1), (0, 1, 0), (-1, 0, 0))
ANCHOR = (0.20, 1.10, -0.50)
OFFSET = (0.03, 0.09, -0.08)

anchor_plain = transform(IDENTITY, ANCHOR)
joint = transform(IDENTITY, OFFSET)
row, plain = matrix_row(anchor_plain, joint, "회전 없음", MUTED)
assert [plain[r][3] for r in range(3)] == [0.23, 1.19, -0.58], plain

s = TOPDOWN_PX_PER_CM
ax, ay = 236, 636
tip = (ax + OFFSET[0] * 100 * s, ay + OFFSET[2] * 100 * s)
inner = hand_top(ax, ay) + arrow(ax, ay, tip[0] - 6, tip[1] + 13, YELLOW, 4)
panel = topdown_panel((ax, ay), inner) + tip_dot(*tip)
panel += t(tip[0] + 26, tip[1] - 6, "(0.23, −0.58)", 17, YELLOW, 650, font=MONO)
panel += t(ax + 40, ay + 26, "(0.20, −0.50)", 17, ACCENT, 650, font=MONO)

body = [heading("숫자로 보는 검지 끝 월드 좌표", "개념도 · 손이 회전하지 않은 경우 · 단위 m"), row, panel]
body.append(rect(546, 400, 498, 276, 22, PANEL, YELLOW, 2))
body.append(rect(546, 400, 6, 276, 3, YELLOW))
body.append(t(574, 436, "columns.3에서 x, y, z 읽기", 21, INK, 650))
body.append(t(574, 462, "월드 원점 기준", 16, MUTED))
for i, (axis, expr, meaning) in enumerate([
    ("x", "0.20 + 0.03 = 0.23", "오른쪽 23cm"),
    ("y", "1.10 + 0.09 = 1.19", "위로 1.19m"),
    ("z", "−0.50 − 0.08 = −0.58", "앞쪽 58cm"),
]):
    y = 508 + i * 44
    body.append(t(578, y, axis, 21, YELLOW, 700, font=MONO))
    body.append(t(612, y, expr, 20, BODY, 400, font=MONO))
    body.append(t(1018, y, meaning, 18, MUTED, 400, "end"))
body.append(f'<path d="M574 618 h444" stroke="{LINE}" stroke-width="2"/>')
body.append(t(574, 652, "회전이 없을 때만 앵커 위치에 그대로 더한 값과 같습니다.", 17, BODY))
figure("fingertip-world-example", "숫자로 보는 검지 끝 월드 좌표",
       "손 앵커 (0.20, 1.10, −0.50)와 앵커 기준 검지 끝 (0.03, 0.09, −0.08)의 변환을 곱해 "
       "월드 좌표 (0.23, 1.19, −0.58)를 columns.3에서 읽는 숫자 예시",
       "".join(body))

anchor_turned = transform(ROT_Y_90, ANCHOR)
row, turned = matrix_row(anchor_turned, joint, "회전 (y축 +90°)", ACCENT)
assert [turned[r][3] for r in range(3)] == [0.12, 1.19, -0.53], turned
# 순서를 바꿔 곱하면 회전이 빠지고 단순히 더한 값이 나옵니다.
assert [matmul(joint, anchor_turned)[r][3] for r in range(3)] == [0.23, 1.19, -0.58]

ax, ay = 330, 636
rotated = [sum(ROT_Y_90[r][k] * OFFSET[k] for k in range(3)) for r in range(3)]
assert [round(v, 6) for v in rotated] == [-0.08, 0.09, -0.03]
true_tip = (ax + rotated[0] * 100 * s, ay + rotated[2] * 100 * s)
naive_tip = (ax + OFFSET[0] * 100 * s, ay + OFFSET[2] * 100 * s)
radius = math.dist((ax, ay), true_tip)
a_start = math.atan2(naive_tip[1] - ay, naive_tip[0] - ax) - math.radians(8)
a_end = math.radians(-150)
a_mid = (a_start + a_end) / 2
arc_start = (ax + radius * math.cos(a_start), ay + radius * math.sin(a_start))
arc_end = (ax + radius * math.cos(a_end), ay + radius * math.sin(a_end))
arc_label = (ax + (radius + 24) * math.cos(a_mid), ay + (radius + 24) * math.sin(a_mid))
inner = (
    hand_top(ax, ay, ghost=True) + hand_top(ax, ay, angle=-90)
    + f'<path d="M{arc_start[0]:.1f} {arc_start[1]:.1f} A{radius:.1f} {radius:.1f} 0 0 0 '
      f'{arc_end[0]:.1f} {arc_end[1]:.1f}" fill="none" stroke="{INK}" stroke-width="3" '
      f'stroke-dasharray="8 7" opacity=".8"/>'
    + head(arc_end[0], arc_end[1], 120, INK, 13)
    + arrow(ax, ay, true_tip[0] + 13, true_tip[1] + 6, YELLOW, 4)
)
panel = topdown_panel((ax, ay), inner)
panel += tip_dot(*naive_tip, "none", MUTED)
panel += tip_dot(*true_tip)
panel += t(arc_label[0], arc_label[1] + 6, "+90°", 19, INK, 700, "middle")
panel += t(naive_tip[0] + 20, naive_tip[1] - 8, "더하기만 하면", 16, ORANGE, 600)
panel += t(naive_tip[0] + 20, naive_tip[1] + 14, "(0.23, −0.58)", 16, ORANGE, 600, font=MONO)
panel += t(true_tip[0] - 20, true_tip[1] - 30, "실제 검지 끝", 16, YELLOW, 650, "end")
panel += t(true_tip[0] - 20, true_tip[1] - 8, "(0.12, −0.53)", 17, YELLOW, 650, "end", font=MONO)

body = [heading("손이 돌아가 있으면 그냥 더할 수 없습니다",
                "개념도 · 손 앵커가 y축을 중심으로 +90° 회전 (위에서 보면 시계 반대 방향)"), row, panel]
body.append(rect(546, 400, 498, 276, 22, PANEL, YELLOW, 2))
body.append(rect(546, 400, 6, 276, 3, YELLOW))
body.append(t(574, 436, "곱셈은 회전을 먼저 적용합니다", 21, INK, 650))
body.append(t(574, 474, "① 손의 회전으로 상대 위치를 돌리고", 17, BODY))
body.append(t(574, 502, "(0.03, 0.09, −0.08) → (−0.08, 0.09, −0.03)", 18, YELLOW, 600, font=MONO))
body.append(t(574, 538, "② 손 앵커 위치를 더합니다", 17, BODY))
body.append(t(574, 566, "+ (0.20, 1.10, −0.50) = (0.12, 1.19, −0.53)", 18, YELLOW, 600, font=MONO))
body.append(f'<path d="M574 586 h444" stroke="{LINE}" stroke-width="2"/>')
body.append(t(574, 618, "그냥 더한 (0.23, 1.19, −0.58)은 약 12cm 어긋납니다.", 17, ORANGE, 600))
body.append(t(574, 646, "곱하는 순서를 바꿔도 회전이 빠져 같은 틀린 값이 나옵니다.", 17, BODY))
body.append(t(574, 668, "그래서 originFromAnchorTransform을 앞에 두고 곱합니다.", 17, BODY))
figure("fingertip-world-rotation", "손이 회전한 경우의 검지 끝 월드 좌표",
       "손 앵커가 y축으로 +90° 돌아가면 같은 상대 위치 (0.03, 0.09, −0.08)가 월드에서 "
       "(−0.08, 0.09, −0.03) 방향이 되어 검지 끝이 (0.12, 1.19, −0.53)이 되는 숫자 예시",
       "".join(body))


# --- 26. 스타터 프로젝트 파일 지도 -----------------------------------------------

def chapter_badge(cx, cy, number, fill=INK):
    return (f'<circle cx="{cx}" cy="{cy}" r="15" fill="{fill}"/>'
            + t(cx, cy + 6, str(number), 16, "#0b1120", 700, "middle"))


def file_item(x, y, w, name, note, chapter=None):
    out = [rect(x, y, w, 52, 12, "#0e1524", LINE, 2),
           t(x + 16, y + 23, name, 16, INK, 600, font=MONO),
           t(x + 16, y + 43, note, 14, MUTED)]
    if chapter is not None:
        out.append(chapter_badge(x + w - 26, y + 26, chapter))
    return "".join(out)


body = [heading("스타터 프로젝트 파일 지도",
                "개념도 · 들어 있는 파일과 직접 작성하는 Chapter (동그라미 숫자)")]
columns = [
    (56, 352, GREEN, "완성본 제공", "읽어 보고 그대로 씁니다", [
        ("AppModel", "앱 상태 · 그리기 켜기/끄기", None),
        ("ControlView", "제어창 화면과 버튼", None),
        ("ConstellationConfiguration", "0.8초 · 3cm 같은 조절값", None),
        ("ConstellationModel", "점과 선을 저장하는 그래프", None),
        ("ExistingPointConnectionDetector", "기존 점에 다시 연결", None),
    ]),
    (424, 300, YELLOW, "일부 제공", "빈 곳만 채웁니다", [
        ("DwellDetector", "update(…)만 비어 있음", 3),
        ("HandConstellationApp", "WindowGroup만 있음", 4),
        ("Info", "손 추적 권한 설명 없음", 1),
    ]),
    (740, 304, ACCENT, "직접 작성", "import Foundation만 있는 빈 파일", [
        ("HandTrackingService", "손 추적 · 검지 끝 좌표", 2),
        ("ConstellationRenderer", "점과 선 엔티티", 3),
        ("ImmersiveCoordinator", "손 입력과 장면 연결", 4),
        ("ImmersiveView", "RealityView", 4),
    ]),
]
for x, w, color, title, note, items in columns:
    body.append(rect(x, 148, w, 402, 22, PANEL, color, 2))
    body.append(rect(x, 148, 6, 402, 3, color))
    body.append(t(x + 26, 190, title, 24, INK, 650))
    body.append(t(x + 26, 216, note, 16, color, 600))
    for i, (name, item_note, chapter) in enumerate(items):
        body.append(file_item(x + 18, 232 + i * 62, w - 36, name, item_note, chapter))
body.append(t(442, 458, "DwellDetector에는 update(…)를 뺀", 15, MUTED))
body.append(t(442, 480, "타입·속성·보조 메서드가 다 있습니다.", 15, MUTED))
body.append(t(758, 508, "빈 파일이어도 스타터는 그대로", 15, MUTED))
body.append(t(758, 530, "빌드되고 제어창이 열립니다.", 15, MUTED))
body.append(rect(56, 566, 988, 110, 20, "#131b2b", LINE, 2))
body.append(t(80, 598, "Chapter별로 직접 쓰는 곳", 19, INK, 650))
body.append(t(1020, 598, "Chapter 1–4는 Simulator로 확인합니다", 16, MUTED, anchor="end"))
steps = [(1, "권한 설명"), (2, "손 추적"), (3, "머무르기 · 렌더러"), (4, "코디네이터 · 공간"),
         (5, "Vision Pro 실행")]
for i, (number, label) in enumerate(steps):
    x = 80 + i * 190
    last = number == 5
    body.append(rect(x, 614, 178, 48, 24, "#0e1524", ORANGE if last else LINE, 2))
    body.append(chapter_badge(x + 24, 638, number, ORANGE if last else INK))
    body.append(t(x + 48, 644, label, 16, INK, 600))
figure("starter-project-files", "스타터 프로젝트 파일 지도",
       "스타터 프로젝트의 파일을 완성본 제공, 일부 제공, 직접 작성으로 나누고 각 파일을 작성하는 "
       "Chapter를 표시한 지도",
       "".join(body))


def rasterize(name, content, svg_path, png_path):
    direct = subprocess.run(
        ["sips", "-s", "format", "png", str(svg_path), "--out", str(png_path)],
        capture_output=True,
    )
    if direct.returncode == 0:
        return
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


def write_figure(name, content):
    svg_path = OUT / f"{name}.svg"
    svg_path.write_text(content, encoding="utf-8")
    rasterize(name, content, svg_path, OUT / f"{name}.png")


def lzw_encode(indices, min_code_size=8):
    """GIF LZW (variable code size, clear when the table is full), as giflib writes it."""
    clear, eoi = 1 << min_code_size, (1 << min_code_size) + 1
    bits = min_code_size + 1
    max_code = 1 << bits
    running = eoi + 1
    table = {}
    out = bytearray()
    buffer = clear
    filled = bits
    prefix = indices[0]
    for pixel in indices[1:]:
        key = (prefix << 8) | pixel
        code = table.get(key)
        if code is not None:
            prefix = code
            continue
        buffer |= prefix << filled
        filled += bits
        while filled >= 8:
            out.append(buffer & 0xFF)
            buffer >>= 8
            filled -= 8
        if running >= max_code and bits < 12:
            bits += 1
            max_code = 1 << bits
        if running >= 4095:
            buffer |= clear << filled
            filled += bits
            while filled >= 8:
                out.append(buffer & 0xFF)
                buffer >>= 8
                filled -= 8
            table.clear()
            running = eoi + 1
            bits = min_code_size + 1
            max_code = 1 << bits
        else:
            table[key] = running
            running += 1
        prefix = pixel
    for code in (prefix, eoi):
        buffer |= code << filled
        filled += bits
        while filled >= 8:
            out.append(buffer & 0xFF)
            buffer >>= 8
            filled -= 8
        if code == prefix and running >= max_code and bits < 12:
            bits += 1
            max_code = 1 << bits
    if filled:
        out.append(buffer & 0xFF)
    return bytes(out)


def gif_from_indexed(frames, palette, transparent, width, height, delays):
    """Writes an animated GIF that stores only the pixels that changed since the last frame.

    ffmpeg's GIF encoder re-sends whole frames when a frame has transparent pixels (the
    rounded corners), so the frame differencing is done here instead.
    """
    def blocks(data):
        out = bytearray([8])
        for i in range(0, len(data), 255):
            chunk = data[i:i + 255]
            out.append(len(chunk))
            out += chunk
        out.append(0)
        return bytes(out)

    out = bytearray(b"GIF89a")
    out += width.to_bytes(2, "little") + height.to_bytes(2, "little") + bytes([0xF7, transparent, 0])
    for r, g, b in palette:
        out += bytes([r, g, b])
    out += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"
    previous = None
    for frame, delay in zip(frames, delays):
        if previous is None:
            left, top, w, h, data = 0, 0, width, height, frame
        else:
            rows = [y for y in range(height)
                    if frame[y * width:(y + 1) * width] != previous[y * width:(y + 1) * width]]
            if not rows:
                left, top, w, h, data = 0, 0, 1, 1, bytes([transparent])
            else:
                top, bottom = rows[0], rows[-1] + 1
                left, right = width, 0
                for y in rows:
                    a, b = frame[y * width:(y + 1) * width], previous[y * width:(y + 1) * width]
                    first = next(x for x in range(width) if a[x] != b[x])
                    last = next(x for x in range(width - 1, -1, -1) if a[x] != b[x])
                    left, right = min(left, first), max(right, last + 1)
                w, h = right - left, bottom - top
                data = bytearray()
                for y in range(top, bottom):
                    a = frame[y * width + left:y * width + right]
                    b = previous[y * width + left:y * width + right]
                    data += bytes(transparent if a[x] == b[x] else a[x] for x in range(w))
                data = bytes(data)
        out += b"\x21\xf9\x04" + bytes([0x05]) + delay.to_bytes(2, "little") + bytes([transparent, 0])
        out += b"\x2c" + b"".join(v.to_bytes(2, "little") for v in (left, top, w, h)) + b"\x00"
        out += blocks(lzw_encode(data))
        previous = frame
    out += b"\x3b"
    return bytes(out)


def write_animation(name, frames, fps):
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    width, height = 880, 576
    with tempfile.TemporaryDirectory(prefix="hand-constellation-gif-") as temporary_directory:
        work = Path(temporary_directory)
        for index, content in enumerate(frames):
            frame_svg = work / f"frame-{index:03d}.svg"
            frame_svg.write_text(content, encoding="utf-8")
            subprocess.run(
                ["sips", "-s", "format", "png", str(frame_svg), "--out",
                 str(work / f"frame-{index:03d}.png")],
                check=True, capture_output=True,
            )
        frames_pattern = str(work / "frame-%03d.png")
        palette_png = work / "palette.png"
        raw = work / "frames.raw"
        subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-framerate", str(fps), "-i", frames_pattern,
             "-vf", "palettegen=max_colors=128:reserve_transparent=1:stats_mode=full",
             str(palette_png)],
            check=True,
        )
        # Bayer dithering is the same at every pixel in every frame, so still areas
        # stay byte-identical between frames and cost nothing in the GIF.
        subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-framerate", str(fps), "-i", frames_pattern,
             "-i", str(palette_png), "-lavfi",
             "paletteuse=dither=bayer:bayer_scale=3:alpha_threshold=128",
             "-f", "rawvideo", "-pix_fmt", "pal8", str(raw)],
            check=True,
        )
        data = raw.read_bytes()
    frame_size = width * height + 1024
    if len(data) != frame_size * len(frames):
        raise SystemExit(f"unexpected raw size {len(data)} for {len(frames)} frames")
    indexed = [data[i * frame_size:i * frame_size + width * height] for i in range(len(frames))]
    argb = data[width * height:frame_size]
    palette, transparent = [], None
    for i in range(256):
        b, g, r, a = argb[i * 4:i * 4 + 4]
        palette.append((r, g, b))
        if a == 0 and transparent is None:
            transparent = i
    if transparent is None:
        raise SystemExit("palette has no transparent entry")
    # 1/12 s is 8.33 cs; 8, 8, 9 keeps the loop at exactly 8 s.
    pattern = [round(100 / fps * (i + 1)) - round(100 / fps * i) for i in range(len(frames))]
    (OUT / f"{name}.gif").write_bytes(
        gif_from_indexed(indexed, palette, transparent, width, height, pattern))


def main() -> None:
    parser = argparse.ArgumentParser(description="Draws the tutorial figures into the DocC catalog.")
    parser.add_argument(
        "--only",
        help="comma-separated figure names to write (e.g. prerequisites,interaction-overview); "
             "other figures are left untouched",
    )
    parser.add_argument("--list", action="store_true", help="print the figure names and exit")
    args = parser.parse_args()

    names = list(FIGURES) + list(ANIMATIONS)
    if args.list:
        print("\n".join(names))
        return
    if args.only:
        selected = [Path(item.strip()).stem if item.strip().endswith((".png", ".svg", ".gif"))
                    else item.strip() for item in args.only.split(",") if item.strip()]
        unknown = [item for item in selected if item not in names]
        if unknown:
            raise SystemExit(f"unknown figure name(s): {', '.join(unknown)} (see --list)")
    else:
        selected = names

    written = []
    for name in selected:
        if name in FIGURES:
            write_figure(name, FIGURES[name])
            written.append(f"{name}.svg/.png")
        else:
            frames, fps = ANIMATIONS[name]()
            write_animation(name, frames, fps)
            written.append(f"{name}.gif ({len(frames)} frames @ {fps} fps)")
    print(f"wrote {len(written)} figure(s): " + ", ".join(written))


if __name__ == "__main__":
    main()
