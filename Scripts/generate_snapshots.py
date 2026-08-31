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
add("C02-T01-AppModel-00.swift", T(XCODE_SWIFT_FILE))
add("C02-T02-AppModel-01.swift", R(A, 1, 6), R(A, 80, 80))
add("C02-T02-AppModel-02.swift", R(A, 1, 11), R(A, 80, 80))
add("C02-T02-AppModel-03.swift", R(A, 1, 20), R(A, 80, 80))
add("C02-T02-AppModel-04.swift", R(A, 1, 25), R(A, 80, 80))
add("C02-T02-AppModel-05.swift", R(A, 1, 27), R(A, 80, 80))
add("C02-T02-AppModel-06.swift", R(A, 1, 35), R(A, 80, 80))
add("C02-T02-AppModel-07.swift", R(A, 1, 55), R(A, 80, 80))
add("C02-T02-AppModel-08.swift", R(A, 1, 63), R(A, 80, 80))
add("C02-T02-AppModel-09.swift", R(A, 1, 72), R(A, 80, 80))
add("C02-T02-AppModel-10.swift", R(A, 1, 80))

# --- Chapter 2: ControlView and the app entry point --------------------------

C = "ControlView.swift"
CV_TAIL = R(C, 195, 200)

add("C02-T03-ControlView-00.swift", T(
    """import SwiftUI

struct ControlView: View {
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
    ControlView()
}
"""))

add("C02-T03-ControlView-01.swift", T(
    """import SwiftUI

/// The window interface for opening, closing, and resetting the experience.
struct ControlView: View {
    @Environment(AppModel.self) private var appModel
    @Environment(\\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\\.dismissImmersiveSpace) private var dismissImmersiveSpace

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
    ControlView()
        .environment(AppModel())
}
"""))

APP = "HandConstellationApp.swift"
add("C02-T03-HandConstellationApp-01.swift", R(APP, 1, 10), R(APP, 12, 12), R(APP, 20, 21))
add("C02-T03-HandConstellationApp-02.swift", R(APP, 1, 13), R(APP, 20, 21))

CLOSE_HSTACK = T("            }\n")

add("C02-T04-ControlView-02.swift", R(C, 1, 15), R(C, 87, 90), CV_TAIL)
add("C02-T04-ControlView-03.swift", R(C, 1, 28), R(C, 87, 90), R(C, 126, 164), CV_TAIL)
add("C02-T04-ControlView-04.swift", R(C, 1, 32), R(C, 87, 90), R(C, 126, 164), CV_TAIL)
add("C02-T04-ControlView-05.swift", R(C, 1, 41), R(C, 87, 90), R(C, 114, 164), CV_TAIL)
add("C02-T04-ControlView-06.swift", R(C, 1, 48), R(C, 87, 90), R(C, 114, 164), CV_TAIL)
add("C02-T04-ControlView-07.swift", R(C, 1, 48), R(C, 87, 90), R(C, 114, 182),
    T("        default:\n            break\n        }\n    }\n"), CV_TAIL)
add("C02-T04-ControlView-08.swift", R(C, 1, 48), R(C, 87, 90), R(C, 114, 194), CV_TAIL)
add("C02-T04-ControlView-09.swift", R(C, 1, 61), CLOSE_HSTACK, R(C, 87, 90), R(C, 91, 105),
    R(C, 114, 194), CV_TAIL)
add("C02-T04-ControlView-10.swift", R(C, 1, 73), CLOSE_HSTACK, R(C, 87, 90), R(C, 91, 194), CV_TAIL)
add("C02-T04-ControlView-11.swift", R(C, 1, 82), R(C, 87, 90), R(C, 91, 194), CV_TAIL)
add("C02-T04-ControlView-12.swift", R(C, 1, 200))

# --- Chapter 3 and 4: HandTrackingService ------------------------------------

H = "HandTrackingService.swift"
H_END = R(H, 123, 123)
H_RET_NIL = T("\n        return nil\n    }\n")

add("C03-T01-HandTrackingService-00.swift", T(XCODE_SWIFT_FILE))
add("C03-T02-HandTrackingService-01.swift", R(H, 1, 17))
add("C03-T02-HandTrackingService-02.swift", R(H, 1, 23), H_END)
add("C03-T02-HandTrackingService-03.swift", R(H, 1, 28), T("    }\n"), H_END)
add("C03-T02-HandTrackingService-04.swift", R(H, 1, 31), T("    }\n"), H_END)
add("C03-T02-HandTrackingService-05.swift", R(H, 1, 40), T("    }\n"), H_END)
add("C03-T02-HandTrackingService-06.swift", R(H, 1, 43), H_END)
add("C03-T02-HandTrackingService-07.swift", R(H, 1, 47), H_END)

add("C03-T03-HandTrackingService-08.swift", R(H, 1, 55), H_RET_NIL, H_END)
add("C03-T03-HandTrackingService-09.swift", R(H, 1, 58), H_RET_NIL, H_END)
add("C03-T03-HandTrackingService-10.swift", R(H, 1, 63), H_RET_NIL, H_END)
add("C03-T03-HandTrackingService-11.swift", R(H, 1, 66), H_END)

add("C04-T05-HandTrackingService-12.swift", R(H, 1, 77), H_RET_NIL, H_END)
add("C04-T05-HandTrackingService-13.swift", R(H, 1, 80), H_RET_NIL, H_END)
add("C04-T05-HandTrackingService-14.swift", R(H, 1, 80), H_RET_NIL, R(H, 118, 123))
add("C04-T05-HandTrackingService-15.swift", R(H, 1, 90), H_RET_NIL, R(H, 118, 123))
add("C04-T05-HandTrackingService-16.swift", R(H, 1, 93), H_RET_NIL, R(H, 118, 123))
add("C04-T05-HandTrackingService-17.swift", R(H, 1, 105),
    T("        }\n\n        return true\n    }\n"), R(H, 118, 123))
add("C04-T05-HandTrackingService-18.swift", R(H, 1, 123))

# --- Chapter 4: ConstellationConfiguration -----------------------------------

G = "ConstellationConfiguration.swift"
add("C04-T01-Configuration-00.swift", T(XCODE_SWIFT_FILE))
add("C04-T02-Configuration-01.swift", R(G, 1, 4), R(G, 17, 17))
add("C04-T02-Configuration-02.swift", R(G, 1, 7), R(G, 17, 17))
add("C04-T02-Configuration-03.swift", R(G, 1, 12), R(G, 17, 17))
add("C04-T02-Configuration-04.swift", R(G, 1, 14), R(G, 17, 17))
add("C04-T02-Configuration-05.swift", R(G, 1, 17))

# --- Chapter 4: DwellDetector ------------------------------------------------

D = "DwellDetector.swift"
D_END = R(D, 125, 125)
D_TAIL = R(D, 111, 131)
D_DEFAULT = T("\n        default:\n            return idleSnapshot\n        }\n    }\n")
D_TEMP_RETURN = T("            return idleSnapshot\n")

add("C04-T01-DwellDetector-00.swift", T(XCODE_SWIFT_FILE))
add("C04-T03-DwellDetector-01.swift", R(D, 1, 5), D_END)
add("C04-T03-DwellDetector-02.swift", R(D, 1, 10), D_END)
add("C04-T03-DwellDetector-03.swift", R(D, 1, 17), D_END)
add("C04-T03-DwellDetector-04.swift", R(D, 1, 23), D_END)
add("C04-T03-DwellDetector-05.swift", R(D, 1, 28), D_END)
add("C04-T03-DwellDetector-06.swift", R(D, 1, 41), D_END)
add("C04-T03-DwellDetector-07.swift", R(D, 1, 41), R(D, 111, 125))
add("C04-T03-DwellDetector-08.swift", R(D, 1, 48),
    T("\n        return idleSnapshot\n    }\n"), D_TAIL)
add("C04-T03-DwellDetector-09.swift", R(D, 1, 58), D_DEFAULT, D_TAIL)
add("C04-T03-DwellDetector-10.swift", R(D, 1, 69), D_TEMP_RETURN, D_DEFAULT, D_TAIL)
add("C04-T03-DwellDetector-11.swift", R(D, 1, 82), D_TEMP_RETURN, D_DEFAULT, D_TAIL)
add("C04-T03-DwellDetector-12.swift", R(D, 1, 90), D_DEFAULT, D_TAIL)
add("C04-T03-DwellDetector-13.swift", R(D, 1, 131))

# --- Chapter 4: FistHoldDetector ---------------------------------------------

F = "FistHoldDetector.swift"
F_END = R(F, 71, 71)
F_TAIL = R(F, 63, 71)
F_RETURN_READY = T("\n        return readySnapshot\n    }\n")
F_DEFAULT = T("\n        default:\n            return readySnapshot\n        }\n    }\n")

add("C04-T01-FistHoldDetector-00.swift", T(XCODE_SWIFT_FILE))
add("C04-T04-FistHoldDetector-01.swift", R(F, 1, 4), F_END)
add("C04-T04-FistHoldDetector-02.swift", R(F, 1, 9), F_END)
add("C04-T04-FistHoldDetector-03.swift", R(F, 1, 15), F_END)
add("C04-T04-FistHoldDetector-04.swift", R(F, 1, 21), F_END)
add("C04-T04-FistHoldDetector-05.swift", R(F, 1, 29), F_END)
add("C04-T04-FistHoldDetector-06.swift", R(F, 1, 29), F_TAIL)
add("C04-T04-FistHoldDetector-07.swift", R(F, 1, 36), F_RETURN_READY, F_TAIL)
add("C04-T04-FistHoldDetector-08.swift", R(F, 1, 41), F_RETURN_READY, F_TAIL)
add("C04-T04-FistHoldDetector-09.swift", R(F, 1, 46), F_DEFAULT, F_TAIL)
add("C04-T04-FistHoldDetector-10.swift", R(F, 1, 54), F_DEFAULT, F_TAIL)
add("C04-T04-FistHoldDetector-11.swift", R(F, 1, 71))

# --- Chapter 5: ConstellationModel -------------------------------------------

M = "ConstellationModel.swift"
M_END = R(M, 81, 81)
M_REJECT = T("\n        return .rejectedInvalidPosition\n    }\n")

add("C05-T01-ConstellationModel-00.swift", T(XCODE_SWIFT_FILE))
add("C05-T02-ConstellationModel-01.swift", R(M, 1, 4), M_END)
add("C05-T02-ConstellationModel-02.swift", R(M, 1, 8), M_END)
add("C05-T02-ConstellationModel-03.swift", R(M, 1, 15), M_END)
add("C05-T02-ConstellationModel-04.swift", R(M, 1, 20), M_END)
add("C05-T02-ConstellationModel-05.swift", R(M, 1, 32), M_END)
add("C05-T02-ConstellationModel-06.swift", R(M, 1, 42), M_END)
add("C05-T02-ConstellationModel-07.swift", R(M, 1, 48), M_REJECT, M_END)
add("C05-T02-ConstellationModel-08.swift", R(M, 1, 52), M_REJECT, M_END)
add("C05-T02-ConstellationModel-09.swift", R(M, 1, 58), M_REJECT, M_END)
add("C05-T02-ConstellationModel-10.swift", R(M, 1, 69), M_END)
add("C05-T02-ConstellationModel-11.swift", R(M, 1, 74), M_END)
add("C05-T02-ConstellationModel-12.swift", R(M, 1, 81))

# --- Chapter 5: ConstellationRenderer ----------------------------------------

N = "ConstellationRenderer.swift"
N_END = R(N, 100, 100)

add("C05-T01-ConstellationRenderer-00.swift", T(XCODE_SWIFT_FILE))
add("C05-T03-ConstellationRenderer-01.swift", R(N, 1, 8), N_END)
add("C05-T03-ConstellationRenderer-02.swift", R(N, 1, 15), N_END)
add("C05-T03-ConstellationRenderer-03.swift", R(N, 1, 20), T("    }\n"), N_END)
add("C05-T03-ConstellationRenderer-04.swift", R(N, 1, 32), T("    }\n"), N_END)
add("C05-T03-ConstellationRenderer-05.swift", R(N, 1, 40), T("    }\n"), N_END)
add("C05-T03-ConstellationRenderer-06.swift", R(N, 1, 45), N_END)
add("C05-T03-ConstellationRenderer-07.swift", R(N, 1, 54), N_END)
add("C05-T03-ConstellationRenderer-08.swift", R(N, 1, 58), N_END)
add("C05-T03-ConstellationRenderer-09.swift", R(N, 1, 73), N_END)
add("C05-T03-ConstellationRenderer-10.swift", R(N, 1, 84), N_END)
add("C05-T03-ConstellationRenderer-11.swift", R(N, 1, 100))

# --- Chapter 6: ImmersiveCoordinator -----------------------------------------

I = "ImmersiveCoordinator.swift"
I_END = R(I, 187, 187)
I_HELPERS = R(I, 176, 187)
I_STATE_HELPERS = R(I, 165, 187)
I_CLOSE_FUNC = T("    }\n")
I_TEMP_CATCH = T(
    "        } catch {\n"
    "            appModel.trackingStatus = .failed(error.localizedDescription)\n"
    "        }\n"
    "    }\n"
)

add("C06-T01-ImmersiveCoordinator-00.swift", T(XCODE_SWIFT_FILE))
add("C06-T02-ImmersiveCoordinator-01.swift", R(I, 1, 9), I_END)
add("C06-T02-ImmersiveCoordinator-02.swift", R(I, 1, 16), I_END)
add("C06-T02-ImmersiveCoordinator-03.swift", R(I, 1, 33), I_END)
add("C06-T02-ImmersiveCoordinator-04.swift", R(I, 1, 33), I_HELPERS)
add("C06-T02-ImmersiveCoordinator-05.swift", R(I, 1, 41), I_TEMP_CATCH, I_HELPERS)
add("C06-T02-ImmersiveCoordinator-06.swift", R(I, 1, 48), I_TEMP_CATCH, I_HELPERS)
add("C06-T02-ImmersiveCoordinator-07.swift", R(I, 1, 52), I_TEMP_CATCH, I_HELPERS)
add("C06-T02-ImmersiveCoordinator-08.swift", R(I, 1, 66), I_HELPERS)
add("C06-T02-ImmersiveCoordinator-09.swift", R(I, 1, 70), I_STATE_HELPERS)
add("C06-T02-ImmersiveCoordinator-10.swift", R(I, 1, 81), I_STATE_HELPERS)
add("C06-T02-ImmersiveCoordinator-11.swift", R(I, 1, 93), I_STATE_HELPERS)

add("C06-T03-ImmersiveCoordinator-12.swift", R(I, 1, 101), I_CLOSE_FUNC, I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-13.swift", R(I, 1, 107), T("        }\n    }\n"), I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-14.swift", R(I, 1, 117), T("        }\n    }\n"), I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-15.swift", R(I, 1, 121), I_CLOSE_FUNC, I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-16.swift", R(I, 1, 127), I_CLOSE_FUNC, I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-17.swift", R(I, 1, 132), I_CLOSE_FUNC, I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-18.swift", R(I, 1, 135), I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-19.swift", R(I, 1, 148), I_CLOSE_FUNC, I_STATE_HELPERS)
add("C06-T03-ImmersiveCoordinator-20.swift", R(I, 1, 187))

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
        "AppModel.swift": "C02-T02-AppModel-10.swift",
        "ControlView.swift": "C02-T04-ControlView-12.swift",
        "HandConstellationApp.swift": "C06-T04-HandConstellationApp-03.swift",
        "HandTrackingService.swift": "C04-T05-HandTrackingService-18.swift",
        "ConstellationConfiguration.swift": "C04-T02-Configuration-05.swift",
        "DwellDetector.swift": "C04-T03-DwellDetector-13.swift",
        "FistHoldDetector.swift": "C04-T04-FistHoldDetector-11.swift",
        "ConstellationModel.swift": "C05-T02-ConstellationModel-12.swift",
        "ConstellationRenderer.swift": "C05-T03-ConstellationRenderer-11.swift",
        "ImmersiveCoordinator.swift": "C06-T03-ImmersiveCoordinator-20.swift",
        "ImmersiveView.swift": "C06-T04-ImmersiveView-04.swift",
    }
    for source, snapshot in finals.items():
        if (SRC / source).read_text(encoding="utf-8") != (OUT / snapshot).read_text(encoding="utf-8"):
            raise SystemExit(f"final snapshot mismatch: {snapshot} != {source}")

    print(f"wrote {written} snapshots; {len(finals)} final snapshots match the app source")


if __name__ == "__main__":
    main()
