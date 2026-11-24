#!/usr/bin/env python3
"""Generates the DocC tutorial illustrations as SVG and rasterizes them to PNG.

Every drawing uses the same dark spatial palette as the existing hero art so
that a page mixing old and new figures still reads as one set.

    python3 Scripts/generate_images.py                      # every figure
    python3 Scripts/generate_images.py --only interaction-dwell,interaction-overview
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
SKIN, SKIN_LIGHT, SKIN_KNUCKLE = "#e9a98f", "#f4b99f", "#eeb39a"


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


def svg(title, desc, body, w=W, h=H, size=None, radial=False):
    """`size` renders the same w×h drawing at another pixel size (used for GIF frames).

    `radial` uses the centred glow background of the cover art instead of the diagonal one.
    """
    out_w, out_h = size or (w, h)
    background = "url(#bgr)" if radial else "url(#bg)"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{out_w}" height="{out_h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
        f'  <title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>\n'
        f'  <defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="#263654"/><stop offset="1" stop-color="#0e111c"/></linearGradient>'
        + (f'<radialGradient id="bgr" cx="50%" cy="38%" r="80%">'
           f'<stop stop-color="#26385c"/><stop offset="1" stop-color="#090c16"/></radialGradient>'
           if radial else "") +
        f'<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">'
        f'<stop stop-color="#ffffff" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="#8adfff" stop-opacity=".07"/></linearGradient>'
        f'<marker id="head" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M1 1 L11 6 L1 11 z" fill="{ACCENT}"/></marker>'
        f'<marker id="headw" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="7" markerHeight="7" '
        f'orient="auto-start-reverse"><path d="M1 1 L11 6 L1 11 z" fill="{MUTED}"/></marker>'
        f'</defs>\n'
        f'  {rect(0, 0, w, h, 52 if radial and w > W else 44, background)}\n  {body}\n</svg>\n'
    )


def heading(text, sub=None):
    out = t(56, 78, text, 34, INK, 700)
    if sub:
        out += t(56, 116, sub, 20, MUTED)
    return out


FIGURES: dict[str, str] = {}


def figure(name, title, desc, body, w=W, h=H, radial=False):
    FIGURES[name] = svg(title, desc, body, w, h, radial=radial)


# --- 앱이 그리는 것 -------------------------------------------------------------
#
# 렌더러(ConstellationRenderer)와 같은 모습으로 그립니다. 점은 흰 구, 선은 흰 원기둥,
# 커서는 반투명 흰 구이고, 기존 점 강조는 더 큰 반투명 흰 구, 미리보기 선은 가늘고 흐린
# 흰 선입니다. 색을 쓰는 것은 글자·화살표·주석뿐입니다. sips는 SVG 필터를 그리지 않으므로
# 빛 번짐은 반투명 원과 선을 겹쳐 흉내 냅니다.

POINT_R = 16
LINE_W = 9
# 커서 1.0배의 반지름(px). 새 점 모드는 0.72배 → 1.42배, 기존 점 연결 모드는 1.0배 → 1.85배.
CURSOR_UNIT = 15.3


def star(x, y, r=POINT_R, opacity=1.0, glow=False):
    halo = ""
    if glow:
        halo = (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 14}" fill="#ffffff" opacity=".07"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 7}" fill="#ffffff" opacity=".13"/>')
    return halo + (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{INK}" stroke="#ffffff" '
                   f'stroke-width="5" opacity="{opacity:.2f}"/>')


def segment(p, q, opacity=0.92, width=LINE_W, glow=False):
    def line(w, op):
        return (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" '
                f'stroke="#ffffff" stroke-width="{w}" stroke-linecap="round" opacity="{op:.2f}"/>')
    halo = line(width + 18, 0.06) + line(width + 9, 0.10) if glow else ""
    return halo + line(width, opacity)


def preview_line(p, q, opacity=0.38):
    """The renderer's preview line: thinner than a real line and mostly transparent."""
    return segment(p, q, opacity, width=5)


def target_highlight(x, y, progress, opacity=1.0):
    """The locked existing point: a larger translucent white sphere that grows to 1.6×."""
    r = 26 * (1 + 0.6 * progress)
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" opacity="{0.2 * opacity:.2f}"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="none" stroke="#ffffff" stroke-width="2" '
            f'opacity="{0.5 * opacity:.2f}"/>')


def cursor_radius(progress=0.0, mode="point", unit=CURSOR_UNIT):
    if mode == "point":
        return unit * (0.72 + 0.70 * progress)
    return unit * (1.0 + 0.85 * progress)


def app_cursor(x, y, progress=0.0, mode="point", unit=CURSOR_UNIT):
    """The fingertip cursor: translucent white while placing points, solid white near a target."""
    r = cursor_radius(progress, mode, unit)
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 9:.1f}" fill="#ffffff" opacity=".10"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ffffff" '
            f'opacity="{0.72 if mode == "point" else 1}"/>')


def letter(x, y, name, size=19):
    """A point name (A, B, C, D) next to a point; a label, so it is not white."""
    return t(x, y, name, size, MUTED, 700, "middle")


def constellation(points, edges, glow=False, names=None, label_offsets=None):
    """Lines first, then points on top, then names. `points` maps a name to (x, y)."""
    out = [segment(points[a], points[b], glow=glow) for a, b in edges]
    out += [star(x, y, glow=glow) for x, y in points.values()]
    if names:
        for name in names:
            x, y = points[name]
            dx, dy = (label_offsets or {}).get(name, (0, -32))
            out.append(letter(x + dx, y + dy, name))
    return "".join(out)


def counts(constellations, points, lines):
    """The control window's count label, character for character."""
    return f"별자리 {constellations}개 · 점 {points}개 · 선 {lines}개"


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


# 첫 실습의 최종 도형: A–B–C–D를 찍고 D–A, A–C를 이어 점 4개 · 선 5개
FIRST_EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("A", "C")]
TRIANGLE_EDGES = [("E", "F"), ("F", "G"), ("G", "E")]


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


def sky(dots):
    return ('<g fill="#9be4ff" opacity=".35">'
            + "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in dots) + "</g>")


def glass(x, y, w, h, rx=30):
    return (rect(x, y, w, h, rx, "#1a2438", None, opacity=0.55)
            + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#glass)" '
              f'stroke="#d8f5ff" stroke-opacity=".35" stroke-width="2"/>')


# --- 표지와 완성 모습 ------------------------------------------------------------
#
# 두 그림 모두 두 번째 실습을 마친 상태(별자리 2개 · 점 7개 · 선 8개)를 그립니다.
# 첫 별자리는 A–B–C–D에 D–A, A–C를 더한 점 4개 · 선 5개, 두 번째는 점 3개 · 선 3개 삼각형입니다.


def cover_hand(tx, ty):
    """The cover art's hand; the cursor sits on the fingertip at local (135, −58)."""
    return (
        f'<g transform="translate({tx} {ty}) rotate(-12)">'
        f'<path d="M0 105C48 60 90 32 120 38c24 5 29 25 18 44l-44 64c-13 20-50 30-79 20z" fill="{SKIN}"/>'
        f'<rect x="111" y="-42" width="48" height="142" rx="24" fill="{SKIN_LIGHT}"/>'
        f'{app_cursor(135, -58, unit=26)}'
        f'</g>'
    )


hero_first = {"A": (150, 560), "B": (285, 320), "C": (480, 385), "D": (520, 600)}
hero_second = {"E": (720, 560), "F": (850, 380), "G": (1010, 530)}
body = [sky([(115, 140, 3), (245, 92, 2), (395, 162, 3), (612, 120, 2), (1080, 330, 3),
             (1120, 660, 2), (180, 740, 3), (640, 260, 2)])]
body.append('<path d="M135 790C340 845 850 844 1070 772" fill="none" stroke="#8adfff" '
            'stroke-opacity=".15" stroke-width="2"/>')
body.append(constellation(hero_first, FIRST_EDGES, glow=True))
body.append(constellation(hero_second, TRIANGLE_EDGES, glow=True))
body.append(cover_hand(760, 700))
body.append(glass(690, 84, 420, 200))
body.append('<circle cx="740" cy="134" r="17" fill="#69dc8e"/>')
body.append(t(772, 144, "그리기 켜짐", 27, "#f6fbff", 700))
body.append(f'<rect x="724" y="180" width="352" height="1" fill="#ffffff" opacity=".18"/>')
icon = [(734, 238), (746, 222), (760, 234)]
body.append(f'<path d="M{icon[0][0]} {icon[0][1]} L{icon[1][0]} {icon[1][1]} L{icon[2][0]} {icon[2][1]}" '
            f'fill="none" stroke="{BODY}" stroke-width="2"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="{BODY}"/>' for x, y in icon))
body.append(t(774, 238, counts(2, 7, 8), 22, "#dbe9f4"))
figure("constellation-hero", "Hand Constellation",
       "오른손 검지 끝의 반투명 흰 커서로 흰 점과 흰 선의 별자리 두 개를 그린 모습과, "
       "그리기 켜짐 · 별자리 2개 · 점 7개 · 선 8개를 표시한 유리 패널",
       "".join(body), 1200, 900, radial=True)

done_first = {"A": (110, 470), "B": (240, 250), "C": (420, 320), "D": (450, 470)}
done_second = {"E": (650, 480), "F": (790, 290), "G": (950, 450)}
body = [constellation(done_first, FIRST_EDGES, glow=True),
        constellation(done_second, TRIANGLE_EDGES, glow=True)]
body.append('<path d="M548 300v170" stroke="#ffffff" stroke-opacity=".24" stroke-width="3" '
            'stroke-dasharray="8 8"/>')
body.append(t(548, 502, "사이에 선 없음", 17, "#9fb2c1", anchor="middle"))
body.append(rect(345, 555, 410, 105, 28, "#ffffff", None, opacity=0.16))
body.append(rect(345, 555, 410, 105, 28, "none", "#ffffff", 1.5, opacity=0.23))
body.append('<circle cx="393" cy="594" r="14" fill="#8c95a3"/>')
body.append(t(420, 603, "그리기 꺼짐", 23, "#e5edf3", 700))
body.append(t(389, 637, counts(2, 7, 8), 18, "#aabac6"))
figure("complete-experience", "완성된 Hand Constellation",
       "그리기를 껐다 켜서 따로 그린 두 별자리(점 4개 · 선 5개, 점 3개 · 선 3개) 사이에 선이 없고, "
       "그리기 꺼짐 · 별자리 2개 · 점 7개 · 선 8개를 표시한 개념도",
       "".join(body), radial=True)

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
body.append(t(88, 594, "ARKit 손 추적은 Apple Vision Pro에서만 동작합니다. 손 추적 권한 창과", 20, BODY))
body.append(t(88, 626, "실제 손으로 점과 선을 그리는 것은 Chapter 5에서 Vision Pro로 확인합니다.", 20, BODY))
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
    ".indexFingerTip 하나만 씁니다.",
    "오른손 검지 끝의 위치가",
    "커서와 새 점의 위치가 됩니다.",
], YELLOW))
body.append(card(700, 418, 344, 220, "각 관절이 주는 것", [
    "isTracked: 지금 추적 중인지",
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
    "손 앵커 → 월드",
], ACCENT))
body.append(t(384, 290, "×", 44, INK, 700, "middle"))
body.append(card(412, 180, 300, 190, "관절 변환", [
    "anchorFromJointTransform",
    "검지 관절 → 손 앵커",
], ACCENT))
body.append(t(740, 290, "=", 44, INK, 700, "middle"))
body.append(card(768, 180, 276, 190, "월드 변환", [
    "검지 관절 → 월드",
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
figure("fingertip-world-transform", "손 앵커 변환과 관절 변환의 곱",
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
    ("기존 점 연결", ACCENT, [
        ("connectionSnapDistance", "0.030 m = 3cm"),
        ("connectionReleaseDistance", "0.040 m = 4cm"),
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
    body.append(rect(x, 170, 316, h, 22, PANEL, color, 2))
    body.append(rect(x, 170, 6, h, 3, color))
    body.append(t(x + 26, 214, title, 25, INK, 650))
    for i, (key, value) in enumerate(rows):
        y = 262 + i * 74
        body.append(t(x + 26, y, key, 17, color, 600, font=MONO))
        body.append(t(x + 26, y + 30, value, 19, BODY))
    x += 336
body.append(rect(56, 596, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 634, "ARKit과 RealityKit의 거리 단위는 미터입니다. 0.015는 1.5cm를 뜻합니다.",
              20, BODY))
# --- 12. 머무르기 상태 머신 -------------------------------------------------------

body = [heading("머무르기 판정 상태 머신", "DwellDetector.State")]
CY = 340
states = [("idle", 150, CY, MUTED), ("dwelling", 520, CY, ACCENT), ("coolingDown", 880, CY, YELLOW)]
for label, cx, cy, color in states:
    body.append(f'<circle cx="{cx}" cy="{cy}" r="88" fill="#131b2b" stroke="{color}" stroke-width="4"/>')
    body.append(t(cx, cy + 8, label, 22, color, 650, "middle", font=MONO))
body.append(arrow(242, CY, 426, CY))
body.append(t(334, CY - 32, "위치가 들어옴", 18, BODY, anchor="middle"))
body.append(arrow(612, CY, 786, CY))
body.append(t(699, CY - 32, "0.8초 유지", 18, BODY, anchor="middle"))
# dwelling 안에서 1.5cm를 벗어나면 그 자리에서 다시 시작
body.append(f'<path d="M474 266 C 510 196, 596 204, 600 290" fill="none" stroke="{ACCENT}" '
            f'stroke-width="5" stroke-linecap="round"/>' + head(600, 290, 87, ACCENT))
body.append(t(618, 236, "1.5cm 벗어나면", 18, BODY))
body.append(t(618, 260, "타이머 재시작", 18, BODY))
# coolingDown에서 3cm 이상 움직이면 새 머무르기
body.append(f'<path d="M880 430 C 840 540, 580 540, 522 432" fill="none" stroke="{ACCENT}" '
            f'stroke-width="5" stroke-linecap="round"/>' + head(522, 432, -119, ACCENT))
body.append(t(700, 548, "3cm 이상 이동", 18, BODY, anchor="middle"))
# trackingLost(): 어느 상태에서든 idle로
body.append(f'<path d="M470 418 C 380 510, 240 490, 178 414" fill="none" stroke="{MUTED}" '
            f'stroke-width="4" stroke-linecap="round"/>' + head(178, 414, -131, MUTED, 13))
body.append(t(324, 514, "검지 위치를 잃으면", 18, MUTED, anchor="middle"))
body.append(f'<path d="M848 258 C 770 104, 262 104, 184 258" fill="none" stroke="{MUTED}" '
            f'stroke-width="4" stroke-linecap="round"/>' + head(184, 258, 117, MUTED, 13))
body.append(t(516, 132, "검지 위치를 잃으면", 18, MUTED, anchor="middle"))
body.append(rect(56, 580, 988, 86, 18, "#131b2b", LINE, 2))
body.append(t(88, 614, "점은 dwelling에서 coolingDown으로 넘어가는 그 한 프레임에만 찍힙니다.",
              19, BODY))
body.append(t(88, 646, "coolingDown 덕분에 같은 자리에서 점이 여러 번 찍히지 않습니다.", 19, MUTED))
figure("dwell-states", "머무르기 판정 상태 머신",
       "idle, dwelling, coolingDown 세 상태와 상태를 바꾸는 조건을 화살표로 이은 그림. "
       "검지 위치를 잃으면 dwelling과 coolingDown 모두 idle로 돌아갑니다",
       "".join(body))

# --- 13. 머무르기 진행 -----------------------------------------------------------
#
# 커서 1.0배를 30px(5mm)로 그립니다. 그러면 1.5cm는 90px, 점(6mm)은 36px입니다.

PROGRESS = "#8edfff"


def progress_arc(cx, cy, r, p):
    if p >= 0.999:
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{PROGRESS}" '
                f'stroke-width="6"/>')
    a = math.radians(-90 + 360 * p)
    ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
    large = 1 if p > 0.5 else 0
    return (f'<path d="M{cx:.1f} {cy - r:.1f} A{r} {r} 0 {large} 1 {ex:.1f} {ey:.1f}" fill="none" '
            f'stroke="{PROGRESS}" stroke-width="6" stroke-linecap="round"/>')


unit = 30
body = [heading("흔들림 허용 범위 1.5cm 안에서 머무르기",
                "개념도 · 머무르는 동안 커서가 커지고, 0.8초가 되면 그 자리에 흰 점이 찍힙니다")]
body.append('<path d="M140 370h820" stroke="#ffffff" stroke-opacity=".13" stroke-width="3"/>')
stages = [(170, 0.0, "머무르기 시작"), (420, 0.5, None), (680, 0.75, None), (930, 1.0, "점 찍힘")]
for x, p, event in stages:
    if p < 1:
        body.append(f'<circle cx="{x}" cy="370" r="{3 * unit}" fill="none" stroke="{ACCENT}" '
                    f'stroke-width="2.5" stroke-dasharray="6 8" opacity=".55"/>')
        body.append(app_cursor(x, 370, p, "point", unit))
        if p > 0:
            ring = cursor_radius(p, "point", unit) + 18
            body.append(f'<circle cx="{x}" cy="370" r="{ring:.1f}" fill="none" stroke="#ffffff" '
                        f'stroke-width="6" opacity=".14"/>')
            body.append(progress_arc(x, 370, round(ring, 1), p))
    else:
        body.append(star(x, 370, r=36, glow=True))
        body.append(f'<circle cx="{x}" cy="370" r="58" fill="none" stroke="#ffffff" stroke-width="3" '
                    f'opacity=".35"/>')
    body.append(t(x, 505, f"{0.8 * p:.1f}초", 21, INK if p < 1 else YELLOW, 600, "middle"))
    body.append(t(x, 535, f"진행률 {p:g}", 17, MUTED, 400, "middle"))
    if event:
        body.append(t(x, 563, event, 17, ACCENT if p < 1 else YELLOW, 650, "middle"))
body.append(t(240, 300, "1.5cm", 17, ACCENT, 650))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 644, "0.8초가 되기 전에 1.5cm 밖으로 나가면 그 자리에서 0초부터 다시 셉니다.", 20, BODY))
figure("dwell-progress", "머무르기 진행",
       "1.5cm 흔들림 허용 범위 안에서 반투명 흰 커서가 0초, 0.4초, 0.6초로 갈수록 커지고 "
       "0.8초에 흰 점이 찍히는 네 단계",
       "".join(body))

# --- 14. 별자리 저장 구조 -----------------------------------------------------

body = [heading("별자리마다 점과 선을 따로 저장하기", "ConstellationModel.constellations: [Constellation]")]
body.append(rect(56, 168, 988, 300, 24, PANEL, LINE, 2))
body.append(t(88, 214, "constellations", 24, INK, 650, font=MONO))
body.append(t(1012, 213, "제어창 표시: " + counts(2, 7, 8), 18, MUTED, anchor="end"))


def storage_line(path):
    return (f'<path d="{path}" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" '
            f'opacity=".85"/>')


y = 250
rows = [
    ("[0]", ["A", "B", "C", "D"], ["M210 {m} H486", "M210 {m} Q348 {b} 486 {m}", "M210 {m} Q302 {a} 394 {m}"],
     (4, 5), "마친 별자리", MUTED),
    ("[1]", [None, None, None], ["M210 {m} H394", "M210 {m} Q302 {b} 394 {m}"], (3, 3), "그리는 중", GREEN),
]
for label, names, paths, (n_points, n_lines), status, status_color in rows:
    m = y + 48
    body.append(rect(88, y, 924, 96, 18, "#0e1524", LINE, 2))
    body.append(t(116, y + 56, label, 22, INK, 650, font=MONO))
    # [0]: A–B–C–D 직선 세 개, D–A(아래 곡선), A–C(위 곡선) / [1]: 직선 두 개와 G–E(아래 곡선)
    for path in paths:
        body.append(storage_line(path.format(m=m, a=y - 24, b=y + 120)))
    for i, name in enumerate(names):
        cx = 210 + i * 92
        body.append(f'<circle cx="{cx}" cy="{m}" r="18" fill="{INK}"/>')
        if name:
            body.append(t(cx, m + 6, name, 16, "#0b1120", 700, "middle"))
    body.append(t(650, y + 56, f"점 {n_points}개 · 선 {n_lines}개", 20, BODY))
    body.append(t(866, y + 56, status, 18, status_color, 650))
    y += 116
body.append(rect(56, 500, 484, 160, 20, "#131b2b", GREEN, 2))
body.append(t(88, 546, "선이 생기는 곳", 22, GREEN, 650))
body.append(t(88, 588, "지금 그리는 Constellation 안의", 19, BODY))
body.append(t(88, 620, "서로 다른 두 점만 잇습니다.", 19, BODY))
body.append(rect(560, 500, 484, 160, 20, "#131b2b", ORANGE, 2))
body.append(t(592, 546, "선이 생기지 않는 곳", 22, ORANGE, 650))
body.append(t(592, 588, "[0]의 마지막 점과 [1]의 첫 점", 19, BODY))
body.append(t(592, 620, "사이에는 선이 없습니다.", 19, BODY))
figure("constellation-storage", "여러 별자리의 저장 구조",
       "constellations 배열의 [0]에 점 4개 · 선 5개, [1]에 점 3개 · 선 3개가 따로 저장되고 "
       "두 별자리 사이에는 선이 없음을 보여 주는 그림",
       "".join(body))

# --- 14b. 제어창과 몰입형 공간 ----------------------------------------------------

body = [glass(56, 105, 370, 455, 34)]
body.append(f'<path d="M104 139 Q106 151 118 153 Q106 155 104 167 Q102 155 90 153 Q102 151 104 139 Z" '
            f'fill="{INK}"/>')
body.append(t(132, 162, "Hand Constellation", 28, "#ffffff", 700))
body.append(t(92, 220, "체험을 시작할 준비가 되었습니다.", 19, "#bcd0df"))
body.append(rect(90, 253, 302, 62, 18, FOCUS))
body.append(t(241, 293, "별자리 그리기 시작", 21, "#ffffff", 650, "middle"))
body.append(rect(90, 335, 145, 58, 17, GREEN, None, opacity=0.4))
body.append(t(162.5, 372, "그리기 켜기", 19, "#ffffff", 650, "middle", opacity=0.6))
body.append(rect(251, 335, 141, 58, 17, "#ffffff", None, opacity=0.08))
body.append(t(321.5, 372, "초기화", 19, BODY, 400, "middle", opacity=0.6))
body.append(t(92, 520, "WindowGroup · 제어창", 18, MUTED))
# 제어창 → 몰입형 공간, 몰입형 공간 → 제어창
body.append(t(533, 262, "별자리 그리기 시작", 13, MUTED, 400, "middle"))
body.append(t(533, 286, "openImmersiveSpace", 15, ACCENT, 600, "middle", font=MONO))
body.append(arrow(446, 300, 616, 300, ACCENT))
body.append(arrow(616, 372, 446, 372, MUTED, 4))
body.append(t(533, 398, "dismissImmersiveSpace", 15, MUTED, 600, "middle", font=MONO))
body.append(t(533, 420, "체험 종료", 13, MUTED, 400, "middle"))
body.append('<defs><clipPath id="space"><rect x="640" y="74" width="404" height="520" rx="42"/>'
            '</clipPath></defs>')
body.append(rect(640, 74, 404, 520, 42, "#070b15"))
body.append(constellation({"A": (690, 405), "B": (750, 255), "C": (905, 285), "D": (870, 410)},
                          FIRST_EDGES))
body.append(f'<g clip-path="url(#space)">{hand(955, 465)}</g>')
body.append(app_cursor(955, 465))
body.append(rect(640, 74, 404, 520, 42, "none", ACCENT, 2, opacity=0.4))
body.append(t(674, 126, "ImmersiveSpace · 혼합 몰입형 공간", 19, "#8edfff", 600))
body.append(t(674, 154, "RealityView · ARKitSession", 16, MUTED))
body.append(t(674, 178, "RealityView와 ARKit은 같은 원점을 씁니다", 15, MUTED))
# 두 장면이 같은 AppModel을 봅니다
body.append(f'<path d="M241 560 V 646 H 420 M842 594 V 646 H 664" fill="none" stroke="{MUTED}" '
            f'stroke-width="2" stroke-dasharray="6 6"/>')
body.append(rect(420, 616, 244, 60, 30, "#131b2b", YELLOW, 2))
body.append(t(542, 642, "같은 AppModel", 17, INK, 650, "middle"))
body.append(t(542, 664, "두 장면이 함께 읽고 씁니다", 13, MUTED, 400, "middle"))
figure("scene-structure", "제어창과 몰입형 공간",
       "WindowGroup으로 띄운 제어창이 openImmersiveSpace로 혼합 몰입형 공간을 열고 dismissImmersiveSpace로 "
       "닫는 구조. 공간 안의 RealityView와 ARKit은 같은 원점을 쓰고, 두 장면은 같은 AppModel을 봅니다. "
       "공간 안의 점, 선, 커서는 흰색입니다.",
       "".join(body))

# --- 15. 엔티티 트리 ----------------------------------------------------------

body = [heading("RealityKit 엔티티 트리", "ConstellationRenderer.rootEntity")]
body.append(rect(400, 170, 300, 96, 20, PANEL, ACCENT, 3))
body.append(t(550, 214, "rootEntity", 24, ACCENT, 650, "middle", font=MONO))
body.append(t(550, 246, "장면에 추가되는 단 하나의 부모", 17, MUTED, anchor="middle"))
# ConstellationRenderer.init의 rootEntity.addChild 순서: 선, 점, 커서, 기존 점 연결 안내(스타터 제공)
children = [
    ("lineContainer", "흰 원기둥으로 그린 선", INK, 36, False),
    ("pointContainer", "흰 구로 그린 점", INK, 292, False),
    ("cursor", "반투명 흰 구 커서", INK, 548, False),
    ("guidanceContainer", "목표 강조·미리보기 선", INK, 804, True),
]
for label, note, color, x, starter in children:
    body.append(f'<path d="M550 266 V 320 H {x+118} V 366" fill="none" stroke="{LINE}" stroke-width="3"/>')
    body.append(rect(x, 366, 236, 118, 20, PANEL, color, 2))
    body.append(t(x + 118, 412, label, 17, color, 650, "middle", font=MONO))
    body.append(t(x + 118, 448, note, 16, BODY, anchor="middle"))
    if starter:
        body.append(rect(x + 138, 354, 90, 24, 12, "#131b2b", YELLOW, 1.5))
        body.append(t(x + 183, 371, "스타터 제공", 13, YELLOW, 600, "middle"))
body.append(rect(56, 528, 988, 132, 20, "#131b2b", LINE, 2))
body.append(t(88, 572, "컨테이너를 나누면", 22, INK, 650))
body.append(t(88, 612, "초기화할 때 찍은 점·선과 연결 안내만 지우고 커서 엔티티는 다시 씁니다.", 20, BODY))
body.append(t(88, 644, "목표 점 강조와 미리보기 선은 guidanceContainer 안에서만 켜고 끕니다.", 20, MUTED))
figure("entity-tree", "RealityKit 엔티티 트리",
       "rootEntity 아래에 선 컨테이너, 점 컨테이너, 커서, 스타터가 제공하는 기존 점 연결 안내 컨테이너가 "
       "차례로 자식으로 붙은 구조도",
       "".join(body))

# --- 15b. 두 점 사이에 선 그리기 ---------------------------------------------------
#
# A(0, 1, −0.5), B(0.06, 1.08, −0.5): z가 같으므로 x–y 평면에서 봅니다. 1m를 1500px로 그립니다.

LINE_A, LINE_B = (0.0, 1.0, -0.5), (0.06, 1.08, -0.5)
diff = tuple(round(b - a, 6) for a, b in zip(LINE_A, LINE_B))
length = math.dist(LINE_A, LINE_B)
mid = tuple(round((a + b) / 2, 6) for a, b in zip(LINE_A, LINE_B))
direction = tuple(round(d / length, 6) for d in diff)
tilt = math.degrees(math.acos(direction[1]))
assert diff == (0.06, 0.08, 0.0) and round(length, 6) == 0.1
assert mid == (0.03, 1.04, -0.5) and direction == (0.6, 0.8, 0.0) and round(tilt) == 37

PX = 1500
half = (diff[0] / 2 * PX, diff[1] / 2 * PX)  # 중점에서 B까지 (45, 60)px


def cylinder(p, q, opacity=0.95, ghost=False):
    """The line entity: a cylinder seen from the side, drawn wider than life so it reads."""
    if ghost:
        return (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="{MUTED}" '
                f'stroke-width="14" stroke-dasharray="6 6" opacity=".55"/>')
    return (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="#ffffff" '
            f'stroke-width="14" opacity="{opacity:.2f}"/>')


body = [heading("두 점 사이에 선 그리기", "개념도 · 원기둥 하나로 두 점을 잇는 방법")]
panels = [
    (56, "① 길이를 정해 만들기", ["높이 = 두 점 사이 거리 0.10", "아직 원점에서 y축 방향으로 섬"],
     "generateCylinder(height:radius:)"),
    (392, "② 중점으로 옮기기", ["중점 (0.03, 1.04, −0.5)", "방향은 아직 y축 그대로"], None),
    (728, "③ 두 점 방향으로 기울이기", ["y축 (0, 1, 0) → 방향 (0.6, 0.8, 0)", "약 37° 기울면 A와 B에 닿음"],
     "simd_quatf(from:to:)"),
]
for index, (x, title, notes, code) in enumerate(panels):
    body.append(rect(x, 150, 316, 370, 24, "#070b15", LINE, 2, opacity=0.72))
    body.append(t(x + 24, 192, title, 20, INK, 650))
    for i, note in enumerate(notes):
        body.append(t(x + 24, 452 + i * 24, note, 16, BODY if i == 0 else MUTED))
    if code:
        body.append(t(x + 24, 504, code, 14, "#8edfff", 500, font=MONO))
    m = (x + 158, 330)
    a = (m[0] - half[0], m[1] + half[1])
    b = (m[0] + half[0], m[1] - half[1])
    top, bottom = (m[0], m[1] - length / 2 * PX), (m[0], m[1] + length / 2 * PX)
    if index == 0:
        body.append(f'<line x1="{m[0]}" y1="422" x2="{m[0]}" y2="230" stroke="{MUTED}" stroke-width="2" '
                    f'stroke-dasharray="5 6"/>' + head(m[0], 224, -90, MUTED, 11))
        body.append(t(m[0] + 12, 234, "y", 16, MUTED, 600))
        body.append(cylinder(top, bottom))
        body.append(f'<circle cx="{m[0]}" cy="{m[1]}" r="5" fill="{ACCENT}"/>')
        body.append(t(m[0] - 18, m[1] + 6, "원점", 15, ACCENT, 600, "end"))
        body.append(f'<path d="M{m[0] + 30} {top[1]} h8 V {bottom[1]} h-8" fill="none" stroke="{ACCENT}" '
                    f'stroke-width="2"/>')
        body.append(t(m[0] + 46, m[1] + 6, "0.10", 16, ACCENT, 650))
    elif index == 1:
        body.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{MUTED}" '
                    f'stroke-width="2" stroke-dasharray="4 6"/>')
        body.append(cylinder(top, bottom))
        body.append(star(*a, r=11) + star(*b, r=11))
        body.append(f'<circle cx="{m[0]}" cy="{m[1]}" r="7" fill="none" stroke="{ACCENT}" stroke-width="3"/>')
        body.append(t(m[0] - 18, m[1] + 6, "중점", 15, ACCENT, 600, "end"))
    else:
        body.append(cylinder(top, bottom, ghost=True))
        body.append(cylinder(a, b))
        body.append(star(*a, r=11) + star(*b, r=11))
        r_arc = 104
        a0, a1 = math.radians(-90), math.atan2(-half[1], half[0])
        p0 = (m[0] + r_arc * math.cos(a0), m[1] + r_arc * math.sin(a0))
        p1 = (m[0] + r_arc * math.cos(a1), m[1] + r_arc * math.sin(a1))
        body.append(f'<line x1="{m[0]}" y1="{top[1]:.1f}" x2="{p0[0]:.1f}" y2="{p0[1] - 6:.1f}" '
                    f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 5"/>')
        body.append(f'<line x1="{b[0]:.1f}" y1="{b[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" '
                    f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 5"/>')
        body.append(f'<path d="M{p0[0]:.1f} {p0[1]:.1f} A{r_arc} {r_arc} 0 0 1 {p1[0]:.1f} {p1[1]:.1f}" '
                    f'fill="none" stroke="{ACCENT}" stroke-width="3"/>')
        body.append(t(p1[0] + 12, p1[1] - 4, "약 37°", 16, ACCENT, 650))
    if index:
        body.append(letter(a[0] - 24, a[1] + 6, "A") + letter(b[0] + 24, b[1] + 6, "B"))
body.append(rect(56, 540, 988, 112, 18, "#131b2b", LINE, 2))
body.append(t(88, 582, "A (0, 1, −0.5) · B (0.06, 1.08, −0.5) · 차이 B − A = (0.06, 0.08, 0)", 19, BODY))
body.append(t(88, 622, "길이 = 차이의 크기 0.10 · 방향 = 차이 ÷ 길이 = (0.6, 0.8, 0) · 단위 m", 19, BODY))
figure("line-between-points", "두 점 사이에 선 그리기",
       "높이 0.10m인 원기둥을 원점에서 y축 방향으로 만들고, A(0, 1, −0.5)와 B(0.06, 1.08, −0.5)의 중점 "
       "(0.03, 1.04, −0.5)로 옮긴 뒤, y축 (0, 1, 0)에서 방향 (0.6, 0.8, 0)으로 약 37° 기울여 두 점을 잇는 세 단계",
       "".join(body))

# --- 17. 입력 처리 순서 -------------------------------------------------------
#
# ImmersiveCoordinator의 process(anchor:appModel:)와 process(position:at:appModel:)의 순서입니다.
# Simulator 빌드에서는 processSimulatedFingertip(appModel:)이 손 앵커 대신 입력 패드의 위치를
# 같은 process(position:at:appModel:)에 넣습니다.

CODE = "#8edfff"
ROW_H, ROW_STEP = 54, 64


def pipeline_row(y, number, title, note, code, color):
    out = [rect(56, y, 760, ROW_H, 14, PANEL, color, 2),
           f'<circle cx="92" cy="{y + 27}" r="16" fill="{color}"/>',
           t(92, y + 33, str(number), 16, "#0b1120", 700, "middle"),
           t(124, y + 23, title, 19, INK, 650),
           t(124, y + 44, note, 15, MUTED),
           t(798, y + 44, code, 14, CODE, 500, "end", font=MONO)]
    return "".join(out)


def pipeline_gap(y):
    return (f'<path d="M436 {y} v 3" stroke="{LINE}" stroke-width="3"/>' + head(436, y + 11, 90, LINE, 9))


body = [heading("한 프레임의 입력 처리 순서", "ImmersiveCoordinator · 오른손 앵커가 들어올 때마다")]
groups = [
    (160, "process(anchor:appModel:)", 172, [
        ("그리기 상태 반영", "그리기를 끄는 순간 지금 그리던 별자리를 마칩니다",
         "applyDrawingState(appModel:)", ORANGE),
        ("그리기가 꺼져 있으면 머무르기를 취소하고 끝", "커서와 기존 점 연결 안내도 함께 숨깁니다",
         "cancelDwell()", MUTED),
        ("검지 끝의 월드 좌표 구하기", "위치를 구할 수 없으면 머무르기를 취소하고 끝",
         "rightIndexFingerTipPosition(from:)", ACCENT),
    ]),
    (390, "process(position:at:appModel:)", 402, [
        ("완료·거절 안내를 유지하는 중이면 여기서 끝", "손이 그 자리를 떠날 때까지 커서만 옮깁니다",
         "keepCompletionVisible · keepRejectionVisible", MUTED),
        ("기존 점 연결을 먼저 확인", "목표에 머무르는 중이면 연결을 처리하고 여기서 끝",
         "connectionDetector.update", GREEN),
        ("새 점 머무르기와 커서", "머무른 시간만큼 커서를 키웁니다",
         "dwellDetector.update · renderer.updateCursor", ACCENT),
        ("점이 찍히면 모델에 더하고, 받아들인 점만 렌더러로 그림", "거절된 점은 제어창 안내로 바뀝니다",
         "constellationModel.addPoint → renderer.addPoint", YELLOW),
    ]),
]
number = 1
for label_y, label, first_y, rows in groups:
    body.append(t(56, label_y, label, 16, CODE, 650, font=MONO))
    y = first_y
    for i, (title, note, code, color) in enumerate(rows):
        body.append(pipeline_row(y, number, title, note, code, color))
        if i < len(rows) - 1:
            body.append(pipeline_gap(y + ROW_H))
        number += 1
        y += ROW_STEP
body.append(f'<path d="M436 {172 + 2 * ROW_STEP + ROW_H} V 394" stroke="{LINE}" stroke-width="3"/>'
            + head(436, 402, 90, LINE, 9))
# Simulator 빌드: 입력 패드의 위치가 같은 process(position:)로 들어옵니다.
body.append(rect(836, 306, 208, 160, 18, "#131b2b", GREEN, 2, dash="7 6"))
body.append(t(856, 336, "Simulator 빌드", 17, GREEN, 650))
for i, line in enumerate(["손 앵커 대신 입력 패드에서", "누른 위치가 여기로", "process(position:)", "들어옵니다."]):
    body.append(t(856, 364 + i * 24, line, 15, BODY, font=MONO if "process" in line else FONT))
body.append(f'<path d="M836 385 H 470" stroke="{GREEN}" stroke-width="2.5" stroke-dasharray="7 6"/>'
            + head(462, 385, 180, GREEN, 11))
figure("input-pipeline", "한 프레임의 입력 처리 순서",
       "process(anchor:appModel:)에서 그리기 상태 반영, 꺼져 있으면 멈춤, 검지 끝 월드 좌표를 거쳐 "
       "process(position:at:appModel:)에서 유지 중인 안내, 기존 점 연결, 새 점 머무르기와 커서, 모델에 더하기와 "
       "렌더링으로 이어지는 순서도. Simulator 빌드에서는 입력 패드의 위치가 같은 process(position:)로 들어온다는 표시",
       "".join(body))

# --- 17b. Simulator 입력 패드 ----------------------------------------------------
#
# 값은 SimulatorInputPad.swift의 SimulatorInputRegion과 같습니다. 패드(360×240pt)에서
# 왼쪽 위를 (0, 0)으로 잰 비율이 몰입형 공간의 0.45m × 0.30m 영역에서 같은 비율 위치가 됩니다.

REGION_SIZE_M = (0.45, 0.30)
REGION_CENTER_M = (-0.42, 1.55, -0.70)
PAD_PT = (360, 240)
assert PAD_PT[1] / PAD_PT[0] == REGION_SIZE_M[1] / REGION_SIZE_M[0]
PRESS = (0.72, 0.38)  # 그림에서 누른 위치 (왼쪽 위 기준 비율)

pad_box = (86, 224, 300, 200)      # x, y, w, h: 패드와 영역을 같은 크기로 그려 비율을 맞춥니다
region_box = (672, 224, 300, 200)


def ratio_point(box, ratio):
    x, y, w, h = box
    return (x + ratio[0] * w, y + ratio[1] * h)


def corner_labels(box):
    x, y, w, h = box
    return (t(x + 10, y + 22, "(0, 0)", 13, MUTED) + t(x + w - 10, y + h - 10, "(1, 1)", 13, MUTED, anchor="end"))


press_label = f"({PRESS[0]:.2f}, {PRESS[1]:.2f})"
body = [heading("입력 패드에서 누른 위치가 검지 끝 위치가 됩니다",
                "개념도 · Simulator 빌드에만 있는 보조 입력")]
# 왼쪽: 제어창 옆에 붙는 입력 패드
body.append(glass(56, 150, 360, 360, 28))
body.append(f'<path d="M84 178 l0 22 l6 -6 l5 10 l4 -2 l-5 -10 l8 0 z" fill="{INK}"/>')
body.append(t(112, 197, "Simulator 입력 패드", 20, INK, 650))
px, py, pw, ph = pad_box
body.append(rect(px, py, pw, ph, 16, "#ffffff", None, opacity=0.08))
body.append(rect(px, py, pw, ph, 16, "none", "#ffffff", 1.5, opacity=0.35))
body.append(corner_labels(pad_box))
dot = ratio_point(pad_box, PRESS)
body.append(f'<circle cx="{dot[0]:.1f}" cy="{dot[1]:.1f}" r="7" fill="#ffffff"/>')
body.append(t(dot[0] - 16, dot[1] + 6, "누른 곳", 15, MUTED, 600, "end"))
body.append(t(dot[0], dot[1] + 34, press_label, 15, BODY, 600, "middle"))
body.append(t(86, 470, f"실제 패드 {PAD_PT[0]} × {PAD_PT[1]}pt · 제어창 오른쪽에 붙습니다", 14, MUTED))
# 오른쪽: 몰입형 공간의 가상 영역
body.append(rect(600, 150, 444, 360, 26, "#070b15", ACCENT, 2, opacity=0.65))
body.append(t(624, 184, "몰입형 공간", 17, "#8edfff", 600))
rx_, ry_, rw_, rh_ = region_box
body.append(rect(rx_, ry_, rw_, rh_, 6, "none", ACCENT, 2.5, dash="8 7"))
body.append(t(rx_ + rw_ / 2, ry_ - 12, f"{REGION_SIZE_M[0]:.2f}m", 16, ACCENT, 650, "middle"))
body.append(t(rx_ + rw_ + 10, ry_ + rh_ / 2 + 6, f"{REGION_SIZE_M[1]:.2f}m", 16, ACCENT, 650))
body.append(corner_labels(region_box))
tip = ratio_point(region_box, PRESS)
body.append(app_cursor(*tip))
body.append(t(tip[0] + 22, tip[1] + 6, "커서", 15, MUTED, 600))
body.append(t(tip[0], tip[1] + 34, press_label, 15, BODY, 600, "middle"))
cx_m, cy_m, cz_m = REGION_CENTER_M
body.append(t(624, 466, f"영역 중심: 원점에서 왼쪽 {abs(cx_m):.2f}m · 높이 {cy_m:.2f}m · 앞 {abs(cz_m):.2f}m",
              15, MUTED))
body.append(t(624, 490, "Simulator 화면에서는 제어창 왼쪽에 보입니다", 15, MUTED))
# 같은 비율 위치로 옮겨집니다
body.append(f'<line x1="{dot[0] + 12:.1f}" y1="{dot[1]:.1f}" x2="{tip[0] - 26:.1f}" y2="{tip[1]:.1f}" '
            f'stroke="{ACCENT}" stroke-width="3" stroke-dasharray="9 7"/>'
            + head(tip[0] - 20, tip[1], 0, ACCENT, 13))
body.append(pill(444, dot[1] + 6, "같은 비율 위치로", ACCENT, 16))
body.append(rect(56, 540, 988, 100, 18, "#131b2b", GREEN, 2))
body.append(t(88, 580, "누른 채 0.8초 멈추면 그 자리에 점이 찍혀요.", 20, INK, 600))
body.append(t(88, 618, "실제 기기에서는 이 자리에 오른손 검지 끝의 위치가 들어옵니다.", 18, BODY))
figure("simulator-input-pad", "Simulator 입력 패드",
       "Simulator 입력 패드에서 왼쪽 위를 기준으로 (0.72, 0.38) 위치를 누르면 몰입형 공간의 "
       "0.45m × 0.30m 영역에서 같은 비율 위치에 커서가 나타나는 개념도",
       "".join(body))

# --- 18. 실행 대상 선택 -------------------------------------------------------

body = [heading("Apple Vision Pro를 실행 대상으로", "개념도 · Xcode 도구 막대의 실행 대상")]
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
    "Team을 본인 팀으로 골랐는지",
    "Bundle Identifier를 본인만 쓰는",
    "값으로 바꿨는지",
    "Vision Pro를 Xcode와 페어링하고",
    "Developer Mode를 켰는지",
]):
    body.append(t(104, 424 + i * 36, line, 19, BODY))
body.append(rect(568, 330, 460, 330, 22, PANEL, ORANGE, 2))
body.append(t(600, 378, "Simulator와 다른 점", 24, ORANGE, 650))
for i, line in enumerate([
    "Simulator에서는 ARKit 손 추적을",
    "쓸 수 없습니다.",
    "손 추적 권한 창과 실제 손으로",
    "점과 선을 그리는 것은",
    "Vision Pro에서 확인합니다.",
]):
    body.append(t(600, 424 + i * 36, line, 19, BODY))
figure("xcode-run-destination", "Apple Vision Pro 실행 대상 선택",
       "Xcode 도구 막대에서 실행 대상으로 Apple Vision Pro를 고른 모습과, 기기 실행 전에 확인할 것, "
       "Simulator와 다른 점을 정리한 개념도",
       "".join(body))

# --- 19. 손 추적 권한 창 ---------------------------------------------------------
#
# 시스템 화면을 그대로 흉내 내지 않고, 앱 이름 · 사용 목적 문장 · 두 버튼만 있는
# 일반적인 대화상자로 그립니다. 사용 목적 문장은 Chapter 1에서 Info 탭에 넣는 값과 같습니다.

PURPOSE = "검지 끝의 움직임을 감지해 공중에 별자리 점과 선을 그리기 위해 손 추적을 사용합니다."
purpose_lines = ["검지 끝의 움직임을 감지해 공중에 별자리 점과 선을", "그리기 위해 손 추적을 사용합니다."]
assert " ".join(purpose_lines) == PURPOSE

body = [heading("처음 공간을 열 때 나오는 손 추적 권한 창",
                "개념도 · 실제 권한 창의 모양은 visionOS 버전에 따라 다릅니다")]
body.append(sky([(820, 170, 2), (980, 150, 3), (1010, 520, 2), (92, 560, 3), (120, 230, 2)]))
body.append('<path d="M96 676C320 712 780 712 1004 668" fill="none" stroke="#8adfff" '
            'stroke-opacity=".15" stroke-width="2"/>')
dx, dy, dw, dh = 150, 150, 580, 380
mid = dx + dw / 2
body.append(rect(dx + 6, dy + 14, dw, dh, 40, "#000000", None, opacity=0.25))
body.append(glass(dx, dy, dw, dh, 40))
body.append(rect(mid - 34, 176, 68, 68, 16, "#16233a", "#d8f5ff", 1.5))
icon = [(mid - 18, 226), (mid - 6, 196), (mid + 14, 212), (mid + 18, 232)]
body.append(f'<path d="M{icon[0][0]} {icon[0][1]} L{icon[1][0]} {icon[1][1]} L{icon[2][0]} {icon[2][1]} '
            f'L{icon[3][0]} {icon[3][1]}" fill="none" stroke="#ffffff" stroke-width="2" opacity=".9"/>'
            + "".join(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#ffffff"/>' for x, y in icon))
body.append(t(mid, 292, "HandConstellation", 28, INK, 700, "middle"))
body.append(t(mid, 324, "손 추적 권한 요청", 18, MUTED, 600, "middle"))
for i, line in enumerate(purpose_lines):
    body.append(t(mid, 378 + i * 30, line, 20, BODY, 400, "middle"))
buttons = [(dx + 28, "허용 안 함", 600), (dx + 302, "허용", 700)]
for bx, label, weight in buttons:
    body.append(rect(bx, 446, 250, 56, 28, "#ffffff", None, opacity=0.14))
    body.append(t(bx + 125, 482, label, 20, INK, weight, "middle"))
allow_x = dx + 302
body.append(rect(allow_x - 6, 440, 262, 68, 34, "none", ACCENT, 3))
results = [(dx + 28 + 125, "확인 필요", ORANGE, "설정에서 다시 허용해야 그릴 수 있습니다"),
           (allow_x + 125, "추적 중", GREEN, "그리기 켜기 버튼을 누를 수 있습니다")]
for cx, chip, color, note in results:
    body.append(arrow(cx, 540, cx, 566, MUTED, 3))
    w = text_width(chip, 18) + 40
    body.append(rect(cx - w / 2, 574, w, 40, 20, "#131b2b", color, 2))
    body.append(t(cx, 600, chip, 18, color, 650, "middle"))
    body.append(t(cx, 646, note, 16, MUTED, 400, "middle"))
body.append(leader(dx + dw + 46, 391, dx + dw, 391))
for i, line in enumerate(["Chapter 1에서 Info 탭에", "적은 사용 목적 문장이", "그대로 나옵니다."]):
    body.append(t(dx + dw + 54, 372 + i * 28, line, 18, BODY))
figure("permission-prompt", "손 추적 권한 창",
       "몰입형 공간을 처음 열 때 나오는 손 추적 권한 창을 일반적인 대화상자로 그린 개념도. "
       "앱 이름 HandConstellation, 사용 목적 문장, 허용 안 함과 허용 버튼, 각 버튼을 눌렀을 때 "
       "제어창의 상태(확인 필요, 추적 중)",
       "".join(body))

# --- 21. 기존 점에 다시 연결 -----------------------------------------------------

body = [heading("기존 점에 다시 연결하기",
                "개념도 · 새 점 대신 이미 찍은 점을 목표로 골라 선만 잇습니다")]
panels = [
    (56, "1. 3cm 안의 점이 목표", counts(1, 3, 2), None),
    (392, "2. 0.8초 머무르기", counts(1, 3, 2), "커서와 강조 표시가 커집니다"),
    (728, "3. 선만 추가", counts(1, 3, 3), "C–A 선이 생깁니다"),
]


def legend_swatch(x, y, color, dash):
    return (f'<line x1="{x}" y1="{y - 5}" x2="{x + 24}" y2="{y - 5}" stroke="{color}" stroke-width="3" '
            f'stroke-dasharray="{dash}"/>')


for index, (x, title, note, annotation) in enumerate(panels):
    pts = {"A": (x + 110, 400), "B": (x + 190, 250), "C": (x + 272, 392)}
    ax, ay = pts["A"]
    body.append(rect(x, 158, 316, 420, 24, "#070b15", LINE, 2, opacity=0.72))
    body.append(t(x + 24, 202, title, 22, INK, 650))
    body.append(t(x + 24, 562, note, 17, MUTED))
    edges = [("A", "B"), ("B", "C")] + ([("C", "A")] if index == 2 else [])
    body.append("".join(segment(pts[a], pts[b]) for a, b in edges))
    if index < 2:
        body.append(preview_line(pts["C"], pts["A"]))
    progress = (0.0, 0.6, 1.0)[index]
    body.append(target_highlight(ax, ay, progress))
    body.append("".join(star(px, py) for px, py in pts.values()))
    body.append(letter(ax - 30, ay + 46, "A") + letter(pts["B"][0] + 28, pts["B"][1] + 6, "B")
                + letter(pts["C"][0] + 30, pts["C"][1] - 22, "C"))
    if index == 0:
        # 3cm 안에 들어오면 목표로 고르고, 4cm 밖으로 나가야 놓습니다.
        body.append(f'<circle cx="{ax}" cy="{ay}" r="{3 * 22}" fill="none" stroke="{ACCENT}" '
                    f'stroke-width="3" stroke-dasharray="6 8"/>')
        body.append(f'<circle cx="{ax}" cy="{ay}" r="{4 * 22}" fill="none" stroke="{MUTED}" '
                    f'stroke-width="2.5" stroke-dasharray="2 7"/>')
        body.append(app_cursor(ax - 38, ay - 26, 0.0, "connection"))
        body.append(leader(x + 40, 300, ax - 46, ay - 40) + t(x + 26, 292, "커서", 14, MUTED, 600))
        body.append(t(x + 204, 428, "미리보기 선", 15, MUTED))
        body.append(legend_swatch(x + 24, 508, ACCENT, "6 8") + t(x + 56, 508, "3cm 안: 목표로 고름", 14, BODY))
        body.append(legend_swatch(x + 24, 532, MUTED, "2 7")
                    + t(x + 56, 532, "4cm 밖으로 나가면 놓음", 14, BODY))
    elif index == 1:
        body.append(app_cursor(ax + 4, ay - 3, 0.6, "connection"))
    if annotation:
        body.append(t(x + 176, 500, annotation, 15, MUTED, 400, "middle"))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", GREEN, 2))
body.append(t(88, 644, "선의 끝은 손가락 위치가 아니라 저장된 점의 위치라서 기존 점과 정확히 만납니다.",
              20, BODY))
figure("closure-snap-feedback", "기존 점에 다시 연결하기",
       "점 C를 찍은 뒤 3cm 안의 기존 점 A가 목표로 강조되고 C–A 미리보기 선이 보이는 장면"
       "(4cm 밖으로 나가면 목표를 놓음), "
       "0.8초 머무르는 동안 커서와 강조가 커지는 장면, 점 수는 그대로 두고 C–A 선만 추가된 장면",
       "".join(body))

# --- 22. 첫 실습의 최종 도형 -----------------------------------------------------

closed = {"A": (150, 470), "B": (262, 255), "C": (480, 300), "D": (530, 495)}
body = [heading("기존 점을 다시 이은 첫 별자리",
                "개념도 · A–B–C–D를 찍은 뒤 D–A, A–C 선을 더한 결과")]
body.append(rect(56, 160, 584, 420, 26, "#070b15", ACCENT, 2, opacity=0.65))
body.append(constellation(closed, FIRST_EDGES, names="ABCD",
                          label_offsets={"A": (-36, 8), "B": (0, -32), "C": (56, 6), "D": (30, 34)}))
body.append(target_highlight(*closed["C"], 1.0))
body.append(leader(507, 230, 488, 262) + pill(440, 222, "연결 완료 표시", INK, 17))
body.append(rect(664, 160, 380, 140, 22, PANEL, GREEN, 2) + rect(664, 160, 6, 140, 3, GREEN))
body.append(t(690, 204, "완료 상태", 25, INK, 650))
body.append(t(690, 246, counts(1, 4, 5), 20, INK, 600))
body.append(t(690, 278, "선: A–B · B–C · C–D · D–A · A–C", 17, MUTED))
body.append(rect(664, 320, 380, 260, 22, PANEL, ACCENT, 2) + rect(664, 320, 6, 260, 3, ACCENT))
body.append(t(690, 364, "제어창 안내", 25, INK, 650))
for y, caption, lines in [
    (402, "기존 점에 연결했을 때", ["기존 점에 연결됐어요.", "이 점에서 계속 그릴 수 있어요."]),
    (496, "이미 선으로 이어진 점을 고르면", ["이미 연결된 점이에요.", "다른 기존 점을 선택해 주세요."]),
]:
    body.append(t(690, y, caption, 16, MUTED))
    for i, line in enumerate(lines):
        body.append(t(690, y + 28 + i * 26, line, 19, BODY))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", LINE, 2))
body.append(t(88, 644, "기존 점에 다시 연결하면 새 점 없이 선만 늘어나므로 점 개수는 4개 그대로입니다.", 20, BODY))
figure("device-closed-triangle", "기존 점을 다시 이은 첫 별자리",
       "흰 점 A, B, C, D와 흰 선 A–B, B–C, C–D, D–A, A–C로 이루어진 별자리 1개 · 점 4개 · 선 5개, "
       "방금 연결한 C의 완료 표시, 제어창 안내 문구",
       "".join(body))

# --- 23. 두 번째 별자리 ------------------------------------------------------

body = [heading("분리된 두 번째 별자리", "개념도 · 그리기를 끄고 다시 켠 뒤 새로 그린 별자리")]
body.append(rect(56, 160, 988, 420, 26, "#070b15", ACCENT, 2, opacity=0.65))
separate_first = {"A": (110, 452), "B": (245, 260), "C": (425, 316), "D": (462, 476)}
separate_second = {"E": (720, 470), "F": (840, 290), "G": (980, 440)}
body.append(constellation(separate_first, FIRST_EDGES, names="ABCD",
                          label_offsets={"A": (-30, 8), "B": (-30, -14), "C": (30, 6), "D": (28, 28)}))
body.append(constellation(separate_second, TRIANGLE_EDGES))
body.append(f'<circle cx="640" cy="418" r="38" fill="none" stroke="{ORANGE}" stroke-width="5"/>')
body.append(f'<path d="M616 394 l48 48" stroke="{ORANGE}" stroke-width="6" stroke-linecap="round"/>')
body.append(t(640, 512, "여기에 선이 없어야 합니다", 20, ORANGE, 650, "middle"))
body.append(t(286, 214, "첫 번째 별자리 · 점 4개 · 선 5개", 21, YELLOW, 650, "middle"))
body.append(t(850, 214, "두 번째 별자리 · 점 3개 · 선 3개", 21, YELLOW, 650, "middle"))
body.append(rect(56, 606, 988, 62, 16, "#131b2b", GREEN, 2))
body.append(t(88, 644, f"제어창에 {counts(2, 7, 8)}가 보이면 두 별자리가 제대로 나뉜 것입니다.",
              20, BODY))
figure("device-second-constellation", "분리된 두 번째 별자리",
       "점 A–D와 선 5개인 첫 번째 별자리와 점 3개 · 선 3개인 두 번째 별자리 사이에 선이 없음을 강조한 개념도",
       "".join(body))


# --- 24. 완성 동작: 커서, 머무르기, 다음 점, 기존 점 연결 ------------------------
#
# interaction-overview.gif 와 세 장의 정지 화면이 같은 장면 함수를 씁니다.
# 1cm를 22px로 그립니다. 점·선·커서·강조·미리보기 선은 위의 "앱이 그리는 것" 함수를 쓰고,
# 둘레의 하늘색 원은 머문 시간을 보여 주는 그림 속 표시일 뿐 앱이 그리지는 않습니다.

SCENE = (56, 148, 988, 432)
PA, PB, PC = (290, 430), (530, 262), (790, 392)
CM = 22
SNAP_R = 3 * CM
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


def cursor(x, y, progress=0.0, mode="point"):
    """The app's cursor plus the figure's timer ring (the ring is an annotation, not app UI)."""
    ring = 36 if mode == "point" else 54
    out = [app_cursor(x, y, progress, mode)]
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


def counter_pill(constellations, points, lines, color=INK):
    label = counts(constellations, points, lines)
    w = text_width(label, 20) + 40
    return (rect(1024 - w, 616, w, 52, 26, "#0e1524", LINE, 2)
            + t(1024 - w / 2, 649, label, 20, color, 650, "middle"))


def hud(step, caption, constellations, points, lines, color=INK):
    return (
        rect(56, 604, 988, 76, 18, "#131b2b", LINE, 2)
        + f'<circle cx="100" cy="642" r="20" fill="{ACCENT}"/>'
        + t(100, 649, str(step), 20, "#0b1120", 700, "middle")
        + t(136, 650, caption, 22, INK, 600)
        + counter_pill(constellations, points, lines, color)
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
        changed = any(0 <= time - at < 0.9 for at in (*PLACED.values(), CONNECTED_AT))
        out.append(hud(step, caption, 1 if n_points else 0, n_points, n_lines,
                       YELLOW if changed else INK))
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
    + leader(250, 352, 263, 402) + pill(96, 338, "0.8초가 되면 이 자리에 흰 점", INK, 19)
)
body = [heading("검지를 멈추고 0.8초 머무르기",
                "개념도 · 머무르는 동안 커서가 커지고, 0.8초가 되면 그 자리에 흰 점이 찍힙니다")]
body.append(interaction_scene(1.30, pops=False, extra=extra,
                              hud_override=hud(2, "1.5cm 안에서 0.8초 머무르면 점이 찍힙니다", 0, 0, 0)))
figure("interaction-dwell", "검지를 멈추고 0.8초 머무르기",
       "검지 끝의 반투명 흰 커서가 한곳에 머무르는 동안 커지고, 둘레의 원이 머문 시간을 보여 주는 개념도",
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
                              hud_override=hud(3, "점 B가 찍히고 A–B 선이 생깁니다", 1, 2, 1,
                                               YELLOW)))
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
                              hud_override=hud(4, "머무르기가 끝나면 C–A 선만 추가됩니다", 1, 3, 2)))
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
    out = [rect(x, y, w, 50, 12, "#0e1524", LINE, 2),
           t(x + 16, y + 22, name, 16, INK, 600, font=MONO),
           t(x + 16, y + 41, note, 14, MUTED)]
    if chapter is not None:
        out.append(chapter_badge(x + w - 24, y + 25, chapter))
    return "".join(out)


def file_group(x, y, w, h, color, title, note, items, title_size=24):
    out = [rect(x, y, w, h, 22, PANEL, color, 2), rect(x, y, 6, h, 3, color),
           t(x + 24, y + 40, title, title_size, INK, 650), t(x + 24, y + 64, note, 15, color, 600)]
    for i, (name, item_note, chapter) in enumerate(items):
        out.append(file_item(x + 16, y + 78 + i * 56, w - 32, name, item_note, chapter))
    return "".join(out)


# TUTORIAL_20261124_STEP_MAP.md 3장의 스타터 상태와 같습니다.
body = [heading("스타터 프로젝트 파일 지도",
                "개념도 · 들어 있는 파일과 직접 작성하는 Chapter (동그라미 숫자)")]
body.append(file_group(56, 140, 320, 420, GREEN, "완성본 제공", "읽어 보고 그대로 씁니다", [
    ("AppModel", "앱 상태 · 그리기 켜기/끄기", None),
    ("ConstellationConfiguration", "0.8초 · 3cm 같은 조절값", None),
    ("ConstellationModel", "점과 선을 저장하는 그래프", None),
    ("ExistingPointConnectionDetector", "기존 점에 다시 연결", None),
    ("SimulatorInputPad", "Simulator 입력 패드", None),
]))
body.append(t(80, 524, "SimulatorInputPad는 Simulator", 15, MUTED))
body.append(t(80, 546, "빌드에만 들어갑니다.", 15, MUTED))
body.append(file_group(392, 140, 360, 420, YELLOW, "일부 제공", "빈 곳만 채웁니다", [
    ("Info", "손 추적 권한 설명 없음", 1),
    ("DwellDetector", "update(…)만 없음", 3),
    ("ConstellationRenderer", "기존 점 연결 안내만 있음", 3),
    ("ImmersiveCoordinator", "속성·init·보조 메서드만 있음", 4),
    ("ControlView", "toggleImmersiveSpace()만 비어 있음", 4),
    ("HandConstellationApp", "WindowGroup만 있음", 4),
]))
body.append(file_group(768, 140, 276, 250, ACCENT, "빈 파일", "import Foundation 한 줄만 있음", [
    ("HandTrackingService", "손 추적 · 검지 끝 좌표", 2),
    ("ImmersiveView", "RealityView", 4),
]))
body.append(t(792, 352, "빈 파일이어도 스타터는 그대로", 15, MUTED))
body.append(t(792, 374, "빌드되고 제어창이 열립니다.", 15, MUTED))
body.append(file_group(768, 404, 276, 156, MUTED, "테스트", "읽기만 하고 Chapter 3에서 실행", [
    ("DwellDetectorTests", "머무르기 테스트 6개", None),
], title_size=22))
body.append(rect(56, 574, 988, 106, 20, "#131b2b", LINE, 2))
body.append(t(80, 606, "Chapter별로 직접 쓰는 곳", 19, INK, 650))
body.append(t(1020, 606, "Chapter 1–4는 Simulator로 확인합니다", 16, MUTED, anchor="end"))
steps = [(1, "권한 설명"), (2, "손 추적"), (3, "머무르기 · 렌더러"), (4, "코디네이터 · 공간"),
         (5, "Vision Pro 실행")]
for i, (number, label) in enumerate(steps):
    x = 80 + i * 190
    last = number == 5
    body.append(rect(x, 620, 178, 48, 24, "#0e1524", ORANGE if last else LINE, 2))
    body.append(chapter_badge(x + 24, 644, number, ORANGE if last else INK))
    body.append(t(x + 48, 650, label, 16, INK, 600))
figure("starter-project-files", "스타터 프로젝트 파일 지도",
       "스타터 프로젝트의 파일을 완성본 제공(AppModel, ConstellationConfiguration, ConstellationModel, "
       "ExistingPointConnectionDetector, SimulatorInputPad), 일부 제공(Info, DwellDetector, "
       "ConstellationRenderer, ImmersiveCoordinator, ControlView, HandConstellationApp), "
       "빈 파일(HandTrackingService, ImmersiveView), 테스트(DwellDetectorTests)로 나누고 "
       "각 파일을 작성하는 Chapter를 표시한 지도",
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
        help="comma-separated figure names to write (e.g. interaction-dwell,interaction-overview); "
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
