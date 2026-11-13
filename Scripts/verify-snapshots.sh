#!/bin/bash
# Read-only by default. Pass --generate explicitly to update code snapshots,
# the starter project files and the starter zip before verification.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--generate" ]]; then
    python3 Scripts/generate_snapshots.py
    python3 Scripts/build_starter_project.py
elif [[ $# -ne 0 ]]; then
    echo "usage: $0 [--generate]" >&2
    exit 2
fi

python3 Scripts/verify_tutorial.py
python3 Scripts/build_starter_project.py --check

if command -v xcrun >/dev/null 2>&1; then
    cd HandConstellation/HandConstellation.docc
    for snapshot in C0*.swift HL-*.swift; do
        xcrun swiftc -parse "$snapshot" >/dev/null 2>&1 \
            || { echo "snapshot does not parse: $snapshot"; exit 1; }
    done
    echo "all snapshots parse as Swift"
fi
