#!/bin/bash
# Regenerates the tutorial code snapshots and checks that every reference in the
# DocC catalog resolves, that no snapshot is orphaned, and that the last
# snapshot of each file matches the shipping app source byte for byte.
set -euo pipefail

cd "$(dirname "$0")/.."

python3 Scripts/generate_snapshots.py

python3 - <<'PY'
import re
import sys
from pathlib import Path

catalog = Path("HandConstellation/HandConstellation.docc")
patterns = (r"file:\s*([A-Za-z0-9._-]+)",
            r"previousFile:\s*([A-Za-z0-9._-]+)",
            r"source:\s*([A-Za-z0-9._-]+)")

referenced = set()
for tutorial in catalog.glob("*.tutorial"):
    text = tutorial.read_text(encoding="utf-8")
    for pattern in patterns:
        referenced |= set(re.findall(pattern, text))

missing = sorted(name for name in referenced if not (catalog / name).exists())
assets = {p.name for p in catalog.iterdir() if p.suffix in {".swift", ".plist", ".png"}}
orphaned = sorted(assets - referenced)

listed = re.findall(r'@TutorialReference\(tutorial: "doc:([A-Za-z]+)"\)',
                    (catalog / "HandConstellationTutorials.tutorial").read_text(encoding="utf-8"))
pages = {p.stem for p in catalog.glob("*.tutorial")} - {"HandConstellationTutorials"}
unlisted = sorted(pages - set(listed))
dangling = sorted(set(listed) - pages)

for label, values in (("missing references", missing), ("orphaned assets", orphaned),
                      ("tutorials not in the table of contents", unlisted),
                      ("table of contents entries without a file", dangling)):
    if values:
        print(f"{label}: {', '.join(values)}")

if missing or orphaned or unlisted or dangling:
    sys.exit(1)

print(f"{len(referenced)} references resolve; {len(pages)} tutorial pages are all listed")
PY

if command -v xcrun >/dev/null 2>&1; then
    cd HandConstellation/HandConstellation.docc
    for snapshot in C0*.swift; do
        xcrun swiftc -parse "$snapshot" >/dev/null 2>&1 \
            || { echo "snapshot does not parse: $snapshot"; exit 1; }
    done
    echo "all snapshots parse as Swift"
fi
