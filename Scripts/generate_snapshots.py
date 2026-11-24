#!/usr/bin/env python3
"""Regenerates the DocC tutorial code snapshots from the shipping app sources.

A file the reader writes is described as a list of regions of the real source,
each tagged with the step that adds it. The snapshot for step N is the source
with every later region left out, so the last snapshot of a file is the app
source itself and step 0 is the file as the starter project ships it. A region
can name the placeholder that stands in its place until its step arrives; the
starter's stubs (``// Chapter 3에서 작성합니다.``) are such placeholders.

Regions are found by the exact text of their first and last lines, searched in
file order, so editing a source file only breaks the generator where an anchor
line itself changes.

Highlight bases (``HL-*.swift``) are a target snapshot with the lines to
highlight removed. A read-only step passes the base as ``previousFile`` so DocC
highlights exactly those lines, because DocC marks the lines that are new
relative to ``previousFile``. DocC keeps one set of highlights per ``file:``
name on a page, so every read-only step gets its own byte-identical copy of the
state it shows.

    python3 Scripts/generate_snapshots.py            # rewrite the catalog snapshots
    python3 Scripts/generate_snapshots.py --report   # also print the step table
    python3 Scripts/generate_snapshots.py --check    # verify the catalog, write nothing

build_starter_project.py and verify_snapshot_builds.py import this module for
the starter state and the ordered step states.
"""

from __future__ import annotations

import difflib
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "HandConstellation"
TESTS = ROOT / "HandConstellationTests"
OUT = SRC / "HandConstellation.docc"


def find_line(lines: list[str], text: str, start: int, label: str) -> int:
    """Index of the first line at or after ``start`` that equals ``text``."""
    for index in range(start, len(lines)):
        if lines[index].rstrip("\n") == text:
            return index
    raise SystemExit(f"{label}: no line {text!r} at or after line {start + 1}")


def find_span(lines: list[str], first: str, last, start: int, label: str) -> tuple[int, int]:
    """Indices of a region that starts at ``first`` and ends at ``last``.

    ``last`` is one line, or several lines found one after another when the
    closing line alone (a lone ``}``) would match too early.
    """
    begin = end = find_line(lines, first, start, label)
    for text in ([] if last is None else [last] if isinstance(last, str) else list(last)):
        end = find_line(lines, text, end, label)
    return begin, end


# --- files the reader writes -------------------------------------------------


@dataclass(frozen=True)
class Part:
    """Lines of the final source that appear at ``step``.

    ``first`` and ``last`` are whole lines including indentation (see
    ``find_span``); without ``last`` the region is one line. ``before`` and
    ``after`` take that many blank lines around the region with it. ``stub`` is
    shown in the region's place from ``stub_from`` until ``step``. A part with
    step 0 is always present and only moves the search position forward.
    """

    step: int
    first: str
    last: str | tuple[str, ...] | None = None
    before: int = 0
    after: int = 0
    stub: str = ""
    stub_from: int = 0


class Written:
    """A source file that the tutorial builds up step by step."""

    def __init__(self, source: str, chapter: int, parts: list[Part]):
        self.source = source
        self.stem = Path(source).stem
        self.chapter = chapter
        self.lines = (SRC / source).read_text(encoding="utf-8").splitlines(keepends=True)
        self.steps = max(part.step for part in parts)
        self.regions: list[tuple[int, int, Part]] = []
        cursor = 0
        for part in parts:
            first, last = find_span(self.lines, part.first, part.last, cursor, source)
            blanks = self.lines[first - part.before : first] + self.lines[last + 1 : last + 1 + part.after]
            first -= part.before
            last += part.after
            if first < cursor or last >= len(self.lines) or any(line.strip() for line in blanks):
                raise SystemExit(f"{source}: region {part.first!r} does not have the blank lines it claims")
            self.regions.append((first, last, part))
            cursor = last + 1

    def state(self, step: int) -> str:
        out: list[str] = []
        cursor = 0
        for first, last, part in self.regions:
            out.extend(self.lines[cursor:first])
            if part.step <= step:
                out.extend(self.lines[first : last + 1])
            elif part.stub and part.stub_from <= step:
                out.append(part.stub)
            cursor = last + 1
        out.extend(self.lines[cursor:])
        return "".join(out)

    def snapshot_name(self, step: int) -> str:
        return f"C{self.chapter:02d}-{self.stem}-{step:02d}.swift"


def chapter_stub(chapter: int) -> str:
    return f"        // Chapter {chapter}에서 작성합니다.\n"


WRITTEN: dict[str, Written] = {}


def written(source: str, chapter: int, *parts: Part) -> None:
    WRITTEN[source] = Written(source, chapter, list(parts))


# Chapter 2. The starter file holds `import Foundation` only.
written(
    "HandTrackingService.swift", 2,
    # 1: the error type the coordinator later turns into a status.
    Part(1, "import ARKit"),
    Part(1, "import simd", "}"),
    # 2: the class, its two ARKit objects, and the support check in start().
    Part(2, "/// Starts ARKit hand tracking and converts right-index anchors into world positions.",
         "        }", before=1),
    # 3: query the authorization, ask once if undetermined, stop unless allowed.
    Part(3, "        var authorization = await session.queryAuthorization(for: [.handTracking])[.handTracking]",
         ("        guard authorization == .allowed else {", "        }"), before=1),
    # 4: run the session, and stop it.
    Part(4, "        try await session.run([provider])", before=1),
    Part(2, "    }"),
    Part(4, "    func stop() {", "    }", before=1),
    # 5: which anchors and joints to ignore.
    Part(5, "    /// Returns the world-space position of a tracked right index fingertip.",
         "        guard indexFingerTip.isTracked else { return nil }", before=1),
    # 6: origin <- anchor <- joint, then the translation column.
    Part(6, "        let originFromIndexFingerTip =",
         "        return position.hasFiniteComponents ? position : nil", before=1,
         stub="\n        // 다음 Step에서 위치를 계산합니다.\n        return nil\n", stub_from=5),
    Part(5, "    }"),
    Part(2, "}"),
)

# Chapter 3. The starter has everything except update(position:at:).
written(
    "DwellDetector.swift", 3,
    # 1: the input guard, the switch, and the `.idle` case.
    Part(1, "    /// Processes a valid fingertip position at a monotonic timestamp.", "            )"),
    # 2: `.dwelling` progress, and the commit after 0.8 s.
    Part(2, "        case .dwelling(let center, let startedAt):", before=1),
    # 3: `.dwelling`, leaving the 1.5 cm radius restarts the dwell.
    Part(3, "            guard simd_distance(center, position) <= stabilityRadius else {", "            }", after=1),
    Part(2, "            let elapsed = max(0, timestamp - startedAt)", "            )"),
    # 4: `.coolingDown` replaces the placeholder that kept the switch exhaustive.
    Part(4, "        case .coolingDown(let committedPosition):", "            )", before=1,
         stub="\n        default:\n            // 나머지 상태는 다음 Step에서 채웁니다.\n            return idleSnapshot\n",
         stub_from=1),
    Part(1, "        }", "    }", after=1),
)

# Chapter 3. The starter has the connection guidance and four stubs that the
# provided code calls: updateCursor, hideCursor, makeLine, connectExistingPoint.
written(
    "ConstellationRenderer.swift", 3,
    # 1: the two containers and what points and lines are made of.
    Part(1, "    private let pointContainer = Entity()",
         "    private let lineMaterial = UnlitMaterial(color: UIColor.white.withAlphaComponent(0.92))", after=1),
    # 2: the fingertip cursor.
    Part(2, "    private let cursor: ModelEntity",
         "    private let connectionCursorMaterial = UnlitMaterial(color: UIColor.white)", after=1),
    Part(1, '        rootEntity.name = "ConstellationRoot"', "        lineRadius = configuration.lineRadius", after=1,
         stub="        // Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.\n\n"),
    Part(2, "        let cursorMesh = MeshResource.generateSphere(radius: configuration.cursorRadius)",
         "        rootEntity.addChild(cursor)", after=1),
    # 3: move, scale and recolor the cursor; hide it.
    Part(3, "        cursor.position = position", "        cursor.isEnabled = true", stub=chapter_stub(3)),
    Part(3, "        cursor.isEnabled = false", stub=chapter_stub(3)),
    # 4: a cylinder between two points.
    Part(4, "        let offset = end - start", "        return line",
         stub=chapter_stub(3) + "        return nil\n"),
    # 5: committed lines and points.
    Part(5, "    private func addLine(from start: SIMD3<Float>, to end: SIMD3<Float>) {",
         ("        pointContainer.addChild(point)", "    }"), after=1),
    Part(5, "        addLine(from: segment.start, to: segment.end)", "        showConnectionCompletion(at: segment.end)",
         stub=chapter_stub(3)),
    # 6: remove everything.
    Part(6, "    /// Removes all committed entities and transient guidance while preserving the cursor.",
         ("        hideCursor()", "    }"), before=1),
    # 7: a sample constellation for the Xcode canvas.
    Part(7, "#Preview {", "}", before=1),
)

# Chapter 4. The starter has the stored properties, init, the helper extension
# and an empty process(position:at:appModel:) for the Simulator input loop.
written(
    "ImmersiveCoordinator.swift", 4,
    # 1: start the service and turn each outcome into a status.
    Part(1, "    private let handTrackingService = HandTrackingService()"),
    Part(1, "    /// Runs until the immersive view task is cancelled or the ARKit sequence ends.",
         "            appModel.trackingStatus = .tracking", before=1),
    # 3: the anchor loop.
    Part(3, "            for await update in handTrackingService.provider.anchorUpdates {",
         ("            if !Task.isCancelled {", "            }"), before=1),
    Part(1, "        } catch HandTrackingServiceError.unsupported {", "    }"),
    # 4: the drawing button and the reset button.
    Part(4, "    func drawingStateChanged(appModel: AppModel) {",
         ("        clearPointLimitFailure(appModel: appModel)", "    }"), before=1),
    # 5: closing the space.
    Part(5, "    /// Ends tracking and returns everything to its initial state when the space closes.",
         "    }", before=1),
    # 2: one hand anchor becomes one fingertip position.
    Part(2, "    /// Turns one right-hand anchor update into this frame's fingertip position.",
         ("        process(position: position, at: timestamp, appModel: appModel)", "    }"), before=1),
    # 6: held feedback, then an existing-point connection.
    Part(6, "        if keepCompletionVisible(at: position, appModel: appModel) { return }",
         "        hideConnectionProgress(appModel: appModel)", stub=chapter_stub(4)),
    # 7: a new point.
    Part(7, "        let dwell = dwellDetector.update(position: position, at: timestamp)", "        }", before=1),
)

# Chapter 4. The starter file holds `import Foundation` only.
written(
    "ImmersiveView.swift", 4,
    # 1: a RealityView that shows the renderer's root entity.
    Part(1, "import RealityKit", "        }", stub="import Foundation\n"),
    # 2: tie the coordinator to the view's lifetime and the two buttons.
    Part(2, "        .task {", ("        .onDisappear {", "        }")),
    Part(1, "    }", "}"),
)

# Chapter 4. The starter has the WindowGroup only.
written(
    "HandConstellationApp.swift", 4,
    Part(1, "        ImmersiveSpace(id: AppModel.immersiveSpaceID) {",
         "        .immersionStyle(selection: .constant(.mixed), in: .mixed)", before=1),
)

# Chapter 4. The starter has the whole window except the body of toggleImmersiveSpace().
written(
    "ControlView.swift", 4,
    # 1: open the space and handle the result.
    Part(1, r"    @Environment(\.openImmersiveSpace) private var openImmersiveSpace"),
    # 2: dismiss the space and return the window to its initial state.
    Part(2, r"    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace"),
    Part(0, "    private func toggleImmersiveSpace() async {"),
    Part(1, "        switch appModel.immersiveSpaceState {", "        case .open:", stub=chapter_stub(4)),
    Part(2, "            appModel.immersiveSpaceState = .transitioning", "            appModel.constellationCount = 0",
         stub="            break\n", stub_from=1),
    Part(1, "        case .transitioning:", "        }"),
)

# Files the starter ships complete; the tutorial only reads them.
PROVIDED = (
    "AppModel.swift",
    "ConstellationConfiguration.swift",
    "ConstellationModel.swift",
    "ExistingPointConnectionDetector.swift",
    "SimulatorInputPad.swift",
)

# The order in which the tutorial pages apply the steps: (page, source, first step, last step).
STEP_ORDER = (
    ("StartingTheHandTrackingSession", "HandTrackingService.swift", 1, 4),
    ("ConvertingTheFingertipToWorldSpace", "HandTrackingService.swift", 5, 6),
    ("DetectingTheDwell", "DwellDetector.swift", 1, 4),
    ("RenderingPointsAndLines", "ConstellationRenderer.swift", 1, 7),
    ("BuildingTheCoordinatorLifecycle", "ImmersiveCoordinator.swift", 1, 7),
    ("ConnectingTheRealityViewAndAppScenes", "ImmersiveView.swift", 1, 2),
    ("ConnectingTheRealityViewAndAppScenes", "HandConstellationApp.swift", 1, 1),
    ("ConnectingTheRealityViewAndAppScenes", "ControlView.swift", 1, 2),
)

# --- test file the starter ships ---------------------------------------------

# The app's tests also build as a Swift package; the starter has one target.
PACKAGE_IMPORT = """#if SWIFT_PACKAGE
@testable import HandConstellationCore
#else
@testable import HandConstellation
#endif
"""
STARTER_TESTS = ("DwellDetectorTests.swift",)


def starter_test_source(name: str) -> str:
    text = (TESTS / name).read_text(encoding="utf-8")
    if text.count(PACKAGE_IMPORT) != 1:
        raise SystemExit(f"HandConstellationTests/{name}: expected one conditional @testable import")
    return text.replace(PACKAGE_IMPORT, "@testable import HandConstellation\n")


# --- states for the starter builder and the build check ----------------------


def sources_at(progress: dict[str, int]) -> dict[str, str]:
    """Every app Swift file, with each written file at the given step (default 0)."""
    files = {name: (SRC / name).read_text(encoding="utf-8") for name in PROVIDED}
    for name, spec in WRITTEN.items():
        files[name] = spec.state(progress.get(name, 0))
    return files


def starter_sources() -> dict[str, str]:
    return sources_at({})


def chapter_end_progress(chapter: int) -> dict[str, int]:
    """Written files a reader has finished by the end of ``chapter``."""
    return {name: spec.steps for name, spec in WRITTEN.items() if spec.chapter <= chapter}


def ordered_states() -> list[tuple[str, dict[str, int]]]:
    """(label, progress) for the starter and then every step in page order."""
    progress: dict[str, int] = {}
    states = [("starter", {})]
    for page, source, first, last in STEP_ORDER:
        if progress.get(source, 0) != first - 1:
            raise SystemExit(f"STEP_ORDER: {source} step {first} does not follow step {progress.get(source, 0)}")
        for step in range(first, last + 1):
            progress[source] = step
            states.append((WRITTEN[source].snapshot_name(step), dict(progress)))
    unfinished = [name for name, spec in WRITTEN.items() if progress.get(name, 0) != spec.steps]
    if unfinished:
        raise SystemExit("STEP_ORDER does not finish: " + ", ".join(unfinished))
    return states


# --- snapshots ---------------------------------------------------------------

SNAPSHOTS: dict[str, str] = {}
HIGHLIGHTS: dict[str, tuple[str, tuple]] = {}


def add(name: str, text: str) -> None:
    if name in SNAPSHOTS or name in HIGHLIGHTS:
        raise SystemExit(f"duplicate snapshot name: {name}")
    SNAPSHOTS[name] = text


def reading(name: str, text: str, base: str, *spans) -> None:
    """Registers a read-only step: its own copy of ``text`` and a highlight base.

    Each span is ``first`` or ``(first, last)``: whole lines, searched in order
    like the parts of a written file.
    """
    add(name, text)
    if base in SNAPSHOTS or base in HIGHLIGHTS:
        raise SystemExit(f"duplicate snapshot name: {base}")
    HIGHLIGHTS[base] = (name, spans)


def embeddings(base: list[str], target: list[str]) -> int:
    """Counts the ways ``base`` occurs in ``target`` as a line subsequence."""
    ways = [1] + [0] * len(base)
    for line in target:
        for index in range(len(base), 0, -1):
            if base[index - 1] == line:
                ways[index] += ways[index - 1]
    return ways[len(base)]


def highlight_base(name: str, target_text: str, spans) -> tuple[str, list[int]]:
    """The target without the highlighted lines, and those lines' numbers."""
    target = target_text.splitlines(keepends=True)
    highlighted: set[int] = set()
    cursor = 0
    for span in spans:
        first, last = (span, None) if isinstance(span, str) else (span[0], span[1:])
        begin, end = find_span(target, first, last, cursor, name)
        highlighted.update(range(begin, end + 1))
        cursor = end + 1

    numbers = sorted(index + 1 for index in highlighted)
    base_lines = [line for index, line in enumerate(target) if index not in highlighted]
    return "".join(base_lines), numbers


def docc_highlights(pairs: list[tuple[str, str]]) -> list[list[int]] | None:
    """The lines DocC highlights for each (previousFile, file) pair.

    DocC highlights the insertions of the Swift standard library's diff, which
    is not hunk-local: removing two blocks can shift the lines it reports for
    either. docc_highlights.swift runs that same diff. Returns ``None`` when no
    Swift compiler is available.
    """
    if shutil.which("xcrun") is None:
        return None
    with tempfile.TemporaryDirectory() as directory:
        tool = Path(directory) / "docc_highlights"
        script = Path(__file__).with_name("docc_highlights.swift")
        subprocess.run(["xcrun", "swiftc", "-O", str(script), "-o", str(tool)], check=True, capture_output=True)
        payload = json.dumps([{"old": old, "new": new} for old, new in pairs]).encode("utf-8")
        result = subprocess.run([str(tool)], input=payload, check=True, capture_output=True)
    return json.loads(result.stdout)


def highlight_bases(verify: bool = True) -> dict[str, tuple[str, str, list[int]]]:
    """Highlight base -> (text, target snapshot, highlighted lines).

    With ``verify``, the lines are checked against DocC's own diff when a Swift
    compiler is available. Without a compiler, a base is accepted only if it
    fits into its target in exactly one way, which is stricter than DocC needs.
    """
    bases = {}
    for name, (target, spans) in HIGHLIGHTS.items():
        text, numbers = highlight_base(name, SNAPSHOTS[target], spans)
        bases[name] = (text, target, numbers)
    if not verify:
        return bases

    actual = docc_highlights([(text, SNAPSHOTS[target]) for text, target, _ in bases.values()])
    for index, (name, (text, target, numbers)) in enumerate(bases.items()):
        if actual is None:
            count = embeddings(text.splitlines(keepends=True), SNAPSHOTS[target].splitlines(keepends=True))
            if count != 1:
                raise SystemExit(f"{name}: lines {describe(numbers)} can be highlighted {count} ways; adjust the spans")
        elif actual[index] != numbers:
            raise SystemExit(
                f"{name}: DocC would highlight lines {describe(actual[index])}, "
                f"not {describe(numbers)}; adjust the spans"
            )
    return bases


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


def provided(name: str) -> str:
    return (SRC / name).read_text(encoding="utf-8")


# Every state of every written file: -00 is the starter, the last is the app source.
for _spec in WRITTEN.values():
    for _step in range(_spec.steps + 1):
        add(_spec.snapshot_name(_step), _spec.state(_step))

# Chapter 1: the usage description as it reads in a property list.
add("C01-Info-01.plist", """<dict>
    <key>NSHandsTrackingUsageDescription</key>
    <string>검지 끝의 움직임을 감지해 공중에 별자리 점과 선을 그리기 위해 손 추적을 사용합니다.</string>
</dict>
""")

# Chapter 1: starter code that is read, not written.
_app = WRITTEN["HandConstellationApp.swift"].state(0)
reading(
    "C01-HandConstellationApp-scenes.swift", _app, "HL-HandConstellationApp-scenes.swift",
    ("    var body: some Scene {", "    }"),
)
reading(
    "C01-HandConstellationApp-environment.swift", _app, "HL-HandConstellationApp-environment.swift",
    "    @State private var appModel = AppModel()",
    "                .environment(appModel)",
)
reading(
    "C01-AppModel-drawing.swift", provided("AppModel.swift"), "HL-AppModel-drawing.swift",
    ("    enum DrawingState: Equatable {", "    }"),
    '    static let immersiveSpaceID = "ConstellationSpace"',
    "    var drawingState: DrawingState = .disabled",
    # The blank lines between these three members stay unhighlighted; one
    # block would let the diff shift onto the `}` and blank line above.
    ("    var isDrawingEnabled: Bool {", "    }"),
    ("    func setDrawingEnabled(_ isEnabled: Bool) {", "    }"),
    ("    func toggleDrawing() {", "    }"),
)
reading(
    "C01-ControlView-toggle.swift", WRITTEN["ControlView.swift"].state(0), "HL-ControlView-toggle.swift",
    "                    Task { await toggleImmersiveSpace() }",
    ("    private func toggleImmersiveSpace() async {", "    }"),
)

# Chapter 3: the types and values DwellDetector.update works with.
_dwell = WRITTEN["DwellDetector.swift"].state(0)
reading(
    "C03-DwellDetector-00-phase.swift", _dwell, "HL-DwellDetector-phase.swift",
    ("    enum Phase: Equatable, Sendable {", "    }"),
    ("    struct Snapshot: Equatable, Sendable {", "    }"),
)
reading(
    "C03-DwellDetector-00-state.swift", _dwell, "HL-DwellDetector-state.swift",
    ("    private enum State: Equatable, Sendable {", "    }"),
    ("    let dwellDuration: TimeInterval", "    private var state: State = .idle"),
)
_configuration = provided("ConstellationConfiguration.swift")
reading(
    "C03-Configuration-dwell.swift", _configuration, "HL-Configuration-dwell.swift",
    ("    var dwellDuration: TimeInterval = 0.8", "    var rearmDistance: Float = 0.030"),
)
reading(
    "C03-DwellDetectorTests-commit.swift", starter_test_source("DwellDetectorTests.swift"),
    "HL-DwellDetectorTests-commit.swift",
    # Only the lines that no other test repeats, so the diff cannot shift.
    "    func testCommitsExactlyOnceAfterDuration() {",
    ("        let committed = detector.update(position: origin, at: 10.8)",
     "        XCTAssertEqual(committed.phase, .coolingDown)"),
)

# Chapter 3: what the renderer starter provides and what it leaves empty.
_renderer = WRITTEN["ConstellationRenderer.swift"].state(0)
reading(
    "C03-ConstellationRenderer-00-guidance.swift", _renderer, "HL-ConstellationRenderer-guidance.swift",
    ("    // 기존 점 연결 안내에 쓰는 엔티티와 재질입니다. 스타터 프로젝트가 제공합니다.",
     "    private var previewSegment: ConstellationModel.Segment?"),
    "        prepareConnectionGuidance(pointRadius: configuration.pointRadius)",
    ("    /// Highlights one locked existing point and previews the prospective edge.",
     "    private func removePreviewLine() {", "    }"),
)
reading(
    "C03-ConstellationRenderer-00-stubs.swift", _renderer, "HL-ConstellationRenderer-stubs.swift",
    "        // Chapter 3에서 점, 선, 커서를 준비하는 코드를 작성합니다.",
    "        // Chapter 3에서 작성합니다.",
    "        // Chapter 3에서 작성합니다.",
    ("        // Chapter 3에서 작성합니다.", "        return nil"),
    "        // Chapter 3에서 작성합니다.",
)
reading(
    "C03-Configuration-rendering.swift", _configuration, "HL-Configuration-rendering.swift",
    ("    var pointRadius: Float = 0.006", "    var cursorRadius: Float = 0.005"),
)

# Chapter 4: what the coordinator starter provides.
_coordinator = WRITTEN["ImmersiveCoordinator.swift"]
reading(
    "C04-ImmersiveCoordinator-00-state.swift", _coordinator.state(0), "HL-ImmersiveCoordinator-state.swift",
    ("    let renderer: ConstellationRenderer", "    private var recentlyConnectedPosition: SIMD3<Float>?"),
    ("    init(configuration: ConstellationConfiguration = .standard) {", "    }"),
)
reading(
    "C04-ImmersiveCoordinator-00-drawing.swift", _coordinator.state(0), "HL-ImmersiveCoordinator-drawing.swift",
    ("    /// Applies a drawing on/off change from the control window once.",
     "    /// Cancels any dwell in progress and hides the cursor and connection guidance.", "    }"),
)
# Shown right after step 1 writes the call to runWithoutHandTracking(appModel:).
reading(
    "C04-ImmersiveCoordinator-01-simulator.swift", _coordinator.state(1), "HL-ImmersiveCoordinator-simulator.swift",
    "            await runWithoutHandTracking(appModel: appModel)",
    ("    /// Handles a runtime that has no hand tracking.", "        #endif", "    }"),
)
# Shown before step 6 writes process(position:at:appModel:).
reading(
    "C04-ImmersiveCoordinator-05-feedback.swift", _coordinator.state(5), "HL-ImmersiveCoordinator-feedback.swift",
    ("    /// Keeps the completion cue until the fingertip leaves the point it just connected to.", "    }"),
    ("    /// Keeps the rejection message until the fingertip leaves the rejected position.", "    }"),
)
reading(
    "C04-ImmersiveCoordinator-05-connection.swift", _coordinator.state(5), "HL-ImmersiveCoordinator-connection.swift",
    ("    /// Shows the highlight, the preview line, and the progress while the fingertip stays on a target.",
     "    }"),
    ("    /// Refuses a target that already has an edge to the active point.", "    }"),
    ("    /// Adds the edge to the model and the scene after a connection dwell completes.",
     "            appModel.drawingGuidance = .connected"),
)
reading(
    "C04-Configuration-connection.swift", _configuration, "HL-Configuration-connection.swift",
    ("    var connectionSnapDistance: Float = 0.030", "    var minimumPointDistance: Float = 0.030"),
)

# Chapter 4: the Simulator input pad.
reading(
    "C04-SimulatorInputPad-region.swift", provided("SimulatorInputPad.swift"), "HL-SimulatorInputPad-region.swift",
    ("    static let center = SIMD3<Float>(-0.42, 1.55, -0.7)", "    static let size = SIMD2<Float>(0.45, 0.30)"),
    ("    static func position(x: Float, y: Float) -> SIMD3<Float> {", "    }"),
)

# The last snapshot of every source the tutorial writes or reads must match
# the shipping source exactly.
FINALS = {name: spec.snapshot_name(spec.steps) for name, spec in WRITTEN.items()}
FINALS.update({
    "AppModel.swift": "C01-AppModel-drawing.swift",
    "ConstellationConfiguration.swift": "C03-Configuration-dwell.swift",
    "SimulatorInputPad.swift": "C04-SimulatorInputPad-region.swift",
})


def generated_names() -> set[str]:
    return set(SNAPSHOTS) | set(HIGHLIGHTS)


def changed_lines(previous: str, current: str) -> tuple[int, int]:
    """(lines added or rewritten, lines removed) going from one snapshot to the next."""
    added = removed = 0
    matcher = difflib.SequenceMatcher(None, previous.splitlines(), current.splitlines(), autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            removed += i2 - i1
            added += j2 - j1
    return added, removed


def step_table() -> list[tuple[str, str, str, int, int, str]]:
    """(page, snapshot, previousFile, added, removed, highlighted lines) for every step in page order."""
    rows = []
    for page, source, first, last in STEP_ORDER:
        spec = WRITTEN[source]
        for step in range(first, last + 1):
            added, removed = changed_lines(spec.state(step - 1), spec.state(step))
            rows.append([page, spec.snapshot_name(step), spec.snapshot_name(step - 1), added, removed, ""])
    actual = docc_highlights([(SNAPSHOTS[row[2]], SNAPSHOTS[row[1]]) for row in rows])
    for row, numbers in zip(rows, actual or []):
        row[5] = describe(numbers)
    return [tuple(row) for row in rows]


def expected_files() -> dict[str, str]:
    """Every generated catalog file and its text.

    The highlights were verified when the files were generated; comparing the
    committed files with these texts needs no compiler.
    """
    files = dict(SNAPSHOTS)
    files.update({name: text for name, (text, _, _) in highlight_bases(verify=False).items()})
    return files


def stale_files() -> list[Path]:
    return sorted(
        path
        for path in OUT.iterdir()
        if path.suffix in {".swift", ".plist"}
        and path.name.startswith(("C0", "HL-"))
        and path.name not in generated_names()
    )


def check() -> list[str]:
    """Problems with the committed catalog snapshots; writes nothing."""
    errors = []
    for name, text in expected_files().items():
        path = OUT / name
        if not path.is_file():
            errors.append(f"missing snapshot {name}; run python3 Scripts/generate_snapshots.py")
        elif path.read_text(encoding="utf-8") != text:
            errors.append(f"snapshot {name} is out of date; run python3 Scripts/generate_snapshots.py")
    errors += [f"snapshot {path.name} is no longer generated; delete it" for path in stale_files()]
    for source, snapshot in FINALS.items():
        if (SRC / source).read_text(encoding="utf-8") != SNAPSHOTS[snapshot]:
            errors.append(f"final snapshot mismatch: {snapshot} != {source}")
    return errors


def main() -> None:
    ordered_states()
    arguments = sys.argv[1:]
    if "--check" in arguments:
        errors = check()
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        if errors:
            raise SystemExit(f"snapshot check failed with {len(errors)} error(s)")
        print(f"{len(SNAPSHOTS)} snapshots and {len(HIGHLIGHTS)} highlight bases are up to date")
        return

    bases = highlight_bases()
    for name, text in SNAPSHOTS.items():
        (OUT / name).write_text(text, encoding="utf-8")
    for name, (text, _, _) in bases.items():
        (OUT / name).write_text(text, encoding="utf-8")

    for source, snapshot in FINALS.items():
        if (SRC / source).read_text(encoding="utf-8") != (OUT / snapshot).read_text(encoding="utf-8"):
            raise SystemExit(f"final snapshot mismatch: {snapshot} != {source}")

    stale = stale_files()
    for path in stale:
        path.unlink()

    print(
        f"wrote {len(SNAPSHOTS)} snapshots and {len(HIGHLIGHTS)} highlight bases; "
        f"{len(FINALS)} final snapshots match the app source"
    )
    print("highlighted lines (previousFile -> file):")
    for name, (_, target, numbers) in bases.items():
        print(f"  {name} -> {target}: lines {describe(numbers)}")
    if stale:
        print("deleted snapshots that are no longer generated: " + ", ".join(path.name for path in stale))

    if "--report" in arguments:
        print("steps (page: file <- previousFile, lines added/removed, lines DocC highlights):")
        for page, name, previous, added, removed, highlighted in step_table():
            print(f"  {page}: {name} <- {previous}  +{added} -{removed}  [{highlighted}]")


if __name__ == "__main__":
    main()
