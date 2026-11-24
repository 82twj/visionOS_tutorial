#!/usr/bin/env python3
"""Type-checks the app at the starter state and after every tutorial code step.

The states come from generate_snapshots.py: the starter project's sources, then
each snapshot applied in the order the pages present them. Every state is
type-checked as the whole app target for visionOS, once for a device and once
for the Simulator (the Simulator build compiles the input-pad code), in Swift 6
mode with warnings treated as errors. A reader who stops after any step
therefore has a project that builds without warnings.

    python3 Scripts/verify_snapshot_builds.py            # every state
    python3 Scripts/verify_snapshot_builds.py --jobs 2   # fewer compilers at once

This checks types, not linking or the Xcode project; the chapter-end builds
with xcodebuild cover those.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import generate_snapshots as snapshots

PLATFORMS = (
    ("device", "xros", "arm64-apple-xros2.0"),
    ("Simulator", "xrsimulator", "arm64-apple-xros2.0-simulator"),
)


def type_check(label: str, progress: dict[str, int], root: Path) -> list[str]:
    """Problems found while type-checking one state on every platform."""
    directory = root / label.replace(".swift", "")
    directory.mkdir()
    paths = []
    for name, text in sorted(snapshots.sources_at(progress).items()):
        path = directory / name
        path.write_text(text, encoding="utf-8")
        paths.append(str(path))

    problems = []
    for platform, sdk, target in PLATFORMS:
        result = subprocess.run(
            [
                "xcrun", "--sdk", sdk, "swiftc", "-typecheck", "-parse-as-library",
                "-swift-version", "6", "-warnings-as-errors", "-D", "DEBUG",
                "-target", target, "-module-name", "HandConstellation", *paths,
            ],
            capture_output=True, text=True,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0 or "warning:" in output:
            problems.append(f"{label} ({platform}):\n{output.replace(str(directory) + os.sep, '')}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="compilers to run at once")
    args = parser.parse_args()

    states = snapshots.ordered_states()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(lambda state: type_check(state[0], state[1], root), states))

    failures = [problem for problems in results for problem in problems]
    for (label, _), problems in zip(states, results):
        print(f"{'FAIL' if problems else 'ok  '} {label}")
    if failures:
        print("\n\n".join(failures), file=sys.stderr)
        raise SystemExit(f"{len(failures)} of {len(states) * len(PLATFORMS)} type checks failed")
    print(f"{len(states)} states type-check for {' and '.join(name for name, _, _ in PLATFORMS)} without warnings")


if __name__ == "__main__":
    main()
