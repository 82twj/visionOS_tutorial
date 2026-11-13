#!/usr/bin/env python3
"""Regenerates the DocC tutorial code snapshots from the shipping app sources.

Every snapshot is assembled from line ranges of the real Swift files so that the
last snapshot of each file is byte-for-byte identical to the app source.

Highlight bases (``HL-*.swift``) are a target snapshot with the lines to
highlight removed. A read-only step passes the base as ``previousFile`` so DocC
highlights exactly those lines, because DocC marks the lines that are new
relative to ``previousFile``.

Files that the starter project ships complete (ConstellationModel,
ExistingPointConnectionDetector) have no snapshots; build_starter_project.py
checks them instead.
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
HIGHLIGHTS: dict[str, tuple] = {}


def add(name: str, *parts):
    if name in SNAPSHOTS or name in HIGHLIGHTS:
        raise SystemExit(f"duplicate snapshot name: {name}")
    SNAPSHOTS[name] = list(parts)


def copy(name: str, original: str):
    """Registers a byte-identical copy of ``original`` under another name.

    DocC keeps one set of highlights per ``file:`` name on a page, so a page
    that reads the same file with two different highlight bases needs a second
    file name for the second reading step.
    """
    if original not in SNAPSHOTS:
        raise SystemExit(f"{name}: unknown original snapshot {original}")
    add(name, *SNAPSHOTS[original])


def highlight(name: str, target: str, *ranges: tuple):
    """Registers a highlight base: ``target`` without the given line ranges.

    Each range is ``(first, last, expected first line)``; the expected text
    guards against highlighting the wrong lines after a source edit.
    """
    if name in SNAPSHOTS or name in HIGHLIGHTS:
        raise SystemExit(f"duplicate snapshot name: {name}")
    if target not in SNAPSHOTS:
        raise SystemExit(f"{name}: unknown target snapshot {target}")
    HIGHLIGHTS[name] = (target, ranges)


def embeddings(base: list[str], target: list[str]) -> int:
    """Counts the ways ``base`` occurs in ``target`` as a line subsequence."""
    ways = [1] + [0] * len(base)
    for line in target:
        for index in range(len(base), 0, -1):
            if base[index - 1] == line:
                ways[index] += ways[index - 1]
    return ways[len(base)]


def highlight_base(name: str, target_text: str, ranges) -> tuple[str, list[int]]:
    """Removes the highlighted lines and proves DocC's diff is unambiguous.

    DocC reports the lines inserted into ``previousFile``. If the base fits
    into the target in more than one way (for example when a removed block
    ends with the same ``}`` and blank line that precede it), the diff may
    highlight a shifted set of lines, so such bases are rejected.
    """
    target = target_text.splitlines(keepends=True)
    highlighted: set[int] = set()
    for first, last, expected in ranges:
        if not 1 <= first <= last <= len(target):
            raise SystemExit(f"{name}: range {first}-{last} outside 1-{len(target)}")
        if target[first - 1].strip() != expected:
            raise SystemExit(f"{name}: line {first} is {target[first - 1].strip()!r}, expected {expected!r}")
        highlighted.update(range(first, last + 1))

    numbers = sorted(highlighted)
    base_lines = [line for number, line in enumerate(target, 1) if number not in highlighted]
    count = embeddings(base_lines, target)
    if count != 1:
        raise SystemExit(f"{name}: lines {describe(numbers)} can be highlighted {count} ways; adjust the ranges")
    return "".join(base_lines), numbers


def describe(numbers: list[int]) -> str:
    spans: list[str] = []
    start = previous = numbers[0]
    for number in numbers[1:] + [None]:
        if number is not None and number == previous + 1:
            previous = number
            continue
        spans.append(f"{start}" if start == previous else f"{start}-{previous}")
        if number is not None:
            start = previous = number
    return ", ".join(spans)


# --- Chapter 1: Info.plist ---------------------------------------------------

add("C01-T04-Info-01.plist", T(
    """<dict>
    <key>NSHandsTrackingUsageDescription</key>
    <string>검지 끝의 움직임을 감지해 공중에 별자리 점과 선을 그리기 위해 손 추적을 사용합니다.</string>
</dict>
"""))

# --- Chapter 1: starter code that is read, not written -----------------------

APP = "HandConstellationApp.swift"
A = "AppModel.swift"
C = "ControlView.swift"

# The starter app entry point: one WindowGroup, no immersive space yet.
add("C02-T03-HandConstellationApp-02.swift", R(APP, 1, 13), R(APP, 20, 21))
# Read with HL-HandConstellationApp-scenes; the plain name is read with
# HL-HandConstellationApp-environment on the same page.
copy("C02-T03-HandConstellationApp-02-scenes.swift", "C02-T03-HandConstellationApp-02.swift")
add("C02-T02-AppModel-12.swift", R(A, 1, 119))
add("C02-T04-ControlView-14.swift", R(C, 1, 242))

highlight(
    "HL-HandConstellationApp-scenes.swift", "C02-T03-HandConstellationApp-02-scenes.swift",
    (8, 14, "var body: some Scene {"),
)
highlight(
    "HL-HandConstellationApp-environment.swift", "C02-T03-HandConstellationApp-02.swift",
    (6, 6, "@State private var appModel = AppModel()"),
    (11, 11, ".environment(appModel)"),
)
highlight(
    "HL-AppModel-drawing.swift", "C02-T02-AppModel-12.swift",
    (22, 25, "enum DrawingState: Equatable {"),
    (61, 61, 'static let immersiveSpaceID = "ConstellationSpace"'),
    (65, 65, "var drawingState: DrawingState = .disabled"),
    # The blank lines between these three members stay unhighlighted; a single
    # 96-109 block would let the diff shift onto the `}` and blank line above.
    (96, 98, "var isDrawingEnabled: Bool {"),
    (100, 105, "func setDrawingEnabled(_ isEnabled: Bool) {"),
    (107, 109, "func toggleDrawing() {"),
)
highlight(
    "HL-ControlView-immersive.swift", "C02-T04-ControlView-14.swift",
    (6, 7, r"@Environment(\.openImmersiveSpace) private var openImmersiveSpace"),
    (207, 236, "private func toggleImmersiveSpace() async {"),
)

# --- Chapter 2: HandTrackingService ------------------------------------------

H = "HandTrackingService.swift"
add("C03-T01-HandTrackingService-00.swift", E("C03-T01-HandTrackingService-00.swift"))
for index in (1, 2, 3, 5, 6, 7):
    name = f"C03-T02-HandTrackingService-{index:02d}.swift"
    add(name, E(name))
for index in (8, 9, 10):
    name = f"C03-T03-HandTrackingService-{index:02d}.swift"
    add(name, E(name))
add("C04-T05-HandTrackingService-19.swift", R(H, 1, 68))

# --- Chapter 3: ConstellationConfiguration (read only) -----------------------

G = "ConstellationConfiguration.swift"
add("C04-T02-Configuration-07.swift", R(G, 1, 16))
highlight(
    "HL-Configuration-dwell.swift", "C04-T02-Configuration-07.swift",
    (5, 7, "var dwellDuration: TimeInterval = 0.8"),
)

# --- Chapter 3: DwellDetector ------------------------------------------------

D = "DwellDetector.swift"
# Keeps the switch exhaustive until the last branch replaces it.
D_REST = T("""        default:
            // 나머지 상태는 다음 단계에서 채웁니다.
            return idleSnapshot
""")
D_END = R(D, 109, 140)

# The starter file: everything except `update(position:at:)`.
add("C04-T07-DwellDetector-00.swift", R(D, 1, 42), R(D, 112, 140))
# Read with HL-DwellDetector-phase and HL-DwellDetector-state on the same page.
copy("C04-T07-DwellDetector-00-phase.swift", "C04-T07-DwellDetector-00.swift")
copy("C04-T07-DwellDetector-00-state.swift", "C04-T07-DwellDetector-00.swift")
# The input guard and a switch that later steps fill state by state.
add("C04-T07-DwellDetector-01.swift", R(D, 1, 50), D_REST, D_END)
# `.idle`: the first valid position starts a dwell.
add("C04-T07-DwellDetector-02.swift", R(D, 1, 59), D_REST, D_END)
# `.dwelling`: leaving the 1.5 cm radius restarts the dwell at the new position.
add("C04-T07-DwellDetector-03.swift", R(D, 1, 69), T("""
            // 진행률은 다음 단계에서 계산합니다.
            return Snapshot(phase: .dwelling, candidatePosition: center, progress: 0, committedPosition: nil)
"""), T("\n"), D_REST, D_END)
# `.dwelling`: progress, and after 0.8 s the point is made and cooldown begins.
add("C04-T07-DwellDetector-04.swift", R(D, 1, 91), D_REST, D_END)
# `.coolingDown` replaces the temporary default branch.
add("C04-T03-DwellDetector-14.swift", R(D, 1, 140))

highlight(
    "HL-DwellDetector-phase.swift", "C04-T07-DwellDetector-00-phase.swift",
    (6, 10, "enum Phase: Equatable, Sendable {"),
    (12, 17, "struct Snapshot: Equatable, Sendable {"),
)
highlight(
    "HL-DwellDetector-state.swift", "C04-T07-DwellDetector-00-state.swift",
    (19, 23, "private enum State: Equatable, Sendable {"),
    (25, 28, "let dwellDuration: TimeInterval"),
)

# --- Chapter 3: ConstellationRenderer ----------------------------------------

N = "ConstellationRenderer.swift"
add("C05-T01-ConstellationRenderer-00.swift", E("C05-T01-ConstellationRenderer-00.swift"))
for index in (2, 4, 5, 6, 8, 10, 11):
    name = f"C05-T03-ConstellationRenderer-{index:02d}.swift"
    add(name, E(name))
add("C05-T03-ConstellationRenderer-13.swift", R(N, 1, 198))

# --- Chapter 4: ImmersiveCoordinator -----------------------------------------

I = "ImmersiveCoordinator.swift"
add("C06-T01-ImmersiveCoordinator-00.swift", E("C06-T01-ImmersiveCoordinator-00.swift"))
I_HOOKS = """
    // Temporary hooks. The next section fills in the input pipeline.
    private func process(anchor: HandAnchor, appModel: AppModel) {}
"""
add("C06-T02-ImmersiveCoordinator-01.swift", R(I, 1, 39), T("}\n"))
add("C06-T02-ImmersiveCoordinator-02.swift", R(I, 1, 73), T(I_HOOKS + "}\n"))
add("C06-T02-ImmersiveCoordinator-03.swift", R(I, 1, 107), T(I_HOOKS + """\
    private func applyDrawingState(appModel: AppModel) {}
    private func syncDrawingGuidance(appModel: AppModel) {}
    private func trackingLost(appModel: AppModel) {}
}
"""))
add("C06-T03-ImmersiveCoordinator-22.swift", R(I, 1, 343))

# --- Chapter 4: ImmersiveView and the app scenes -----------------------------

V = "ImmersiveView.swift"
V_END = R(V, 26, 27)

add("C06-T01-ImmersiveView-00.swift", T(XCODE_SWIFT_FILE))
add("C06-T04-ImmersiveView-01.swift", R(V, 1, 7), R(V, 9, 12), V_END)
add("C06-T04-ImmersiveView-02.swift", R(V, 1, 15), V_END)
add("C06-T04-ImmersiveView-04.swift", R(V, 1, 27))

add("C06-T04-HandConstellationApp-03.swift", R(APP, 1, 21))

# The last snapshot of every tutorial-written or tutorial-read file must match
# the shipping source exactly.
FINALS = {
    "AppModel.swift": "C02-T02-AppModel-12.swift",
    "ControlView.swift": "C02-T04-ControlView-14.swift",
    "HandConstellationApp.swift": "C06-T04-HandConstellationApp-03.swift",
    "HandTrackingService.swift": "C04-T05-HandTrackingService-19.swift",
    "ConstellationConfiguration.swift": "C04-T02-Configuration-07.swift",
    "DwellDetector.swift": "C04-T03-DwellDetector-14.swift",
    "ConstellationRenderer.swift": "C05-T03-ConstellationRenderer-13.swift",
    "ImmersiveCoordinator.swift": "C06-T03-ImmersiveCoordinator-22.swift",
    "ImmersiveView.swift": "C06-T04-ImmersiveView-04.swift",
}


def generated_names() -> set[str]:
    return set(SNAPSHOTS) | set(HIGHLIGHTS)


def main() -> None:
    rendered = {name: render(parts) for name, parts in SNAPSHOTS.items()}
    for name, text in rendered.items():
        (OUT / name).write_text(text, encoding="utf-8")

    report: list[str] = []
    for name, (target, ranges) in HIGHLIGHTS.items():
        base, numbers = highlight_base(name, rendered[target], ranges)
        (OUT / name).write_text(base, encoding="utf-8")
        report.append(f"  {name} -> {target}: lines {describe(numbers)}")

    for source, snapshot in FINALS.items():
        if (SRC / source).read_text(encoding="utf-8") != (OUT / snapshot).read_text(encoding="utf-8"):
            raise SystemExit(f"final snapshot mismatch: {snapshot} != {source}")

    stale = sorted(
        path.name
        for path in OUT.iterdir()
        if path.suffix in {".swift", ".plist"}
        and path.name.startswith(("C0", "HL-"))
        and path.name not in generated_names()
    )

    print(
        f"wrote {len(rendered)} snapshots and {len(HIGHLIGHTS)} highlight bases; "
        f"{len(FINALS)} final snapshots match the app source"
    )
    print("highlighted lines (previousFile -> file):")
    print("\n".join(report))
    if stale:
        print("not generated (delete or add to SNAPSHOTS): " + ", ".join(stale))


if __name__ == "__main__":
    main()
