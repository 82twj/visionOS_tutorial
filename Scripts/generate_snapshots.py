#!/usr/bin/env python3
"""Regenerates the DocC tutorial code snapshots from the shipping app sources.

Every snapshot is assembled from line ranges of the real Swift files so that the
last snapshot of each file is byte-for-byte identical to the app source.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "HandConstellation"
OUT = SRC / "HandConstellation.docc"

_cache: dict[str, list[str]] = {}


def lines(name: str) -> list[str]:
    if name not in _cache:
        _cache[name] = (SRC / name).read_text(encoding="utf-8").splitlines(keepends=True)
    return _cache[name]


def R(name: str, start: int, end: int) -> tuple:
    """Inclusive, 1-indexed line range of a real source file."""
    return ("src", name, start, end)


def T(text: str) -> tuple:
    """Temporary scaffolding that a later snapshot replaces."""
    return ("raw", text)


def E(name: str) -> tuple:
    """Preserves a previously published intermediate snapshot."""
    return T((OUT / name).read_text(encoding="utf-8"))


def render(parts) -> str:
    out = []
    for part in parts:
        if part[0] == "src":
            _, name, start, end = part
            src = lines(name)
            if end > len(src):
                raise SystemExit(f"{name}: range {start}-{end} exceeds {len(src)} lines")
            out.append("".join(src[start - 1 : end]))
        else:
            out.append(part[1])
    return "".join(out)


# --- shared scaffolding ------------------------------------------------------

XCODE_SWIFT_FILE = "import Foundation\n"

SNAPSHOTS: dict[str, list] = {}


def add(name: str, *parts):
    if name in SNAPSHOTS:
        raise SystemExit(f"duplicate snapshot name: {name}")
    SNAPSHOTS[name] = list(parts)


# --- Chapter 1: starter code -------------------------------------------------

add("C01-T03-ContentView-00.swift", T(
    """import SwiftUI

struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, world!")
        }
        .padding()
    }
}

#Preview(windowStyle: .automatic) {
    ContentView()
}
"""))

add("C01-T03-HandConstellationApp-00.swift", T(
    """import SwiftUI

@main
struct HandConstellationApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
"""))

add("C01-T04-Info-00.plist", T(
    """<dict>
</dict>
"""))

add("C01-T04-Info-01.plist", T(
    """<dict>
    <key>NSHandsTrackingUsageDescription</key>
    <string>검지 끝의 움직임을 감지해 공중에 별자리 점과 선을 그리기 위해 손 추적을 사용합니다.</string>
</dict>
"""))

# --- Chapter 2: AppModel -----------------------------------------------------

A = "AppModel.swift"
add("C02-T01-AppModel-00.swift", E("C02-T01-AppModel-00.swift"))
add("C02-T02-AppModel-12.swift", R(A, 1, 119))

# --- Chapter 2: ControlView and the app entry point --------------------------

C = "ControlView.swift"
add("C02-T03-ControlView-00.swift", E("C02-T03-ControlView-00.swift"))
add("C02-T03-ControlView-01.swift", E("C02-T03-ControlView-01.swift"))

APP = "HandConstellationApp.swift"
add("C02-T03-HandConstellationApp-01.swift", R(APP, 1, 10), R(APP, 12, 12), R(APP, 20, 21))
add("C02-T03-HandConstellationApp-02.swift", R(APP, 1, 13), R(APP, 20, 21))

add("C02-T04-ControlView-14.swift", R(C, 1, 242))

# --- Chapter 3 and 4: HandTrackingService ------------------------------------

H = "HandTrackingService.swift"
add("C03-T01-HandTrackingService-00.swift", E("C03-T01-HandTrackingService-00.swift"))
for index in range(1, 8):
    name = f"C03-T02-HandTrackingService-{index:02d}.swift"
    add(name, E(name))
for index in range(8, 12):
    name = f"C03-T03-HandTrackingService-{index:02d}.swift"
    add(name, E(name))
add("C04-T05-HandTrackingService-19.swift", R(H, 1, 68))

# --- Chapter 4: ConstellationConfiguration -----------------------------------

G = "ConstellationConfiguration.swift"
add("C04-T01-Configuration-00.swift", E("C04-T01-Configuration-00.swift"))
for index in (1, 2):
    name = f"C04-T02-Configuration-{index:02d}.swift"
    add(name, E(name))
add("C04-T02-Configuration-07.swift", R(G, 1, 16))

# --- Chapter 4: DwellDetector ------------------------------------------------

D = "DwellDetector.swift"
add("C04-T01-DwellDetector-00.swift", E("C04-T01-DwellDetector-00.swift"))
for index in range(1, 14):
    name = f"C04-T03-DwellDetector-{index:02d}.swift"
    add(name, E(name))
add("C04-T03-DwellDetector-14.swift", R(D, 1, 140))

# --- Chapter 4: existing-point connection detector --------------------------

L = "ExistingPointConnectionDetector.swift"
add("C04-T01-ExistingPointConnectionDetector-00.swift", T(XCODE_SWIFT_FILE))
add("C04-T06-ExistingPointConnectionDetector-01.swift", R(L, 1, 142))

# --- Chapter 5: ConstellationModel -------------------------------------------

M = "ConstellationModel.swift"
add("C05-T01-ConstellationModel-00.swift", E("C05-T01-ConstellationModel-00.swift"))
for index in range(1, 13):
    name = f"C05-T02-ConstellationModel-{index:02d}.swift"
    add(name, E(name))
add("C05-T02-ConstellationModel-13.swift", E("C05-T02-ConstellationModel-13.swift"))
add("C05-T02-ConstellationModel-14.swift", R(M, 1, 211))

# --- Chapter 5: ConstellationRenderer ----------------------------------------

N = "ConstellationRenderer.swift"
add("C05-T01-ConstellationRenderer-00.swift", E("C05-T01-ConstellationRenderer-00.swift"))
for index in range(1, 12):
    name = f"C05-T03-ConstellationRenderer-{index:02d}.swift"
    add(name, E(name))
add("C05-T03-ConstellationRenderer-12.swift", E("C05-T03-ConstellationRenderer-12.swift"))
add("C05-T03-ConstellationRenderer-13.swift", R(N, 1, 198))

# --- Chapter 6: ImmersiveCoordinator -----------------------------------------

I = "ImmersiveCoordinator.swift"
add("C06-T01-ImmersiveCoordinator-00.swift", E("C06-T01-ImmersiveCoordinator-00.swift"))
add("C06-T03-ImmersiveCoordinator-22.swift", R(I, 1, 343))

# --- Chapter 6: ImmersiveView and the app scenes -----------------------------

V = "ImmersiveView.swift"
V_END = R(V, 26, 27)

add("C06-T01-ImmersiveView-00.swift", T(XCODE_SWIFT_FILE))
add("C06-T04-ImmersiveView-01.swift", R(V, 1, 7), R(V, 9, 12), V_END)
add("C06-T04-ImmersiveView-02.swift", R(V, 1, 15), V_END)
add("C06-T04-ImmersiveView-03.swift", R(V, 1, 21), V_END)
add("C06-T04-ImmersiveView-04.swift", R(V, 1, 27))

add("C06-T04-HandConstellationApp-03.swift", R(APP, 1, 21))


def main() -> None:
    written = 0
    for name, parts in SNAPSHOTS.items():
        (OUT / name).write_text(render(parts), encoding="utf-8")
        written += 1

    # The last snapshot of every file must match the shipping source exactly.
    finals = {
        "AppModel.swift": "C02-T02-AppModel-12.swift",
        "ControlView.swift": "C02-T04-ControlView-14.swift",
        "HandConstellationApp.swift": "C06-T04-HandConstellationApp-03.swift",
        "HandTrackingService.swift": "C04-T05-HandTrackingService-19.swift",
        "ConstellationConfiguration.swift": "C04-T02-Configuration-07.swift",
        "DwellDetector.swift": "C04-T03-DwellDetector-14.swift",
        "ExistingPointConnectionDetector.swift": "C04-T06-ExistingPointConnectionDetector-01.swift",
        "ConstellationModel.swift": "C05-T02-ConstellationModel-14.swift",
        "ConstellationRenderer.swift": "C05-T03-ConstellationRenderer-13.swift",
        "ImmersiveCoordinator.swift": "C06-T03-ImmersiveCoordinator-22.swift",
        "ImmersiveView.swift": "C06-T04-ImmersiveView-04.swift",
    }
    for source, snapshot in finals.items():
        if (SRC / source).read_text(encoding="utf-8") != (OUT / snapshot).read_text(encoding="utf-8"):
            raise SystemExit(f"final snapshot mismatch: {snapshot} != {source}")

    print(f"wrote {written} snapshots; {len(finals)} final snapshots match the app source")


if __name__ == "__main__":
    main()
