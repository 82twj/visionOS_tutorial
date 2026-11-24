#!/bin/bash
# Read-only by default. Pass --generate explicitly to update code snapshots,
# the starter project files and the starter zip before verification.
# Pass --builds to also type-check the app after every tutorial code step.
set -euo pipefail

cd "$(dirname "$0")/.."

builds=false
for argument in "$@"; do
    case "$argument" in
        --generate)
            python3 Scripts/generate_snapshots.py
            python3 Scripts/build_starter_project.py
            ;;
        --builds)
            builds=true
            ;;
        *)
            echo "usage: $0 [--generate] [--builds]" >&2
            exit 2
            ;;
    esac
done

python3 Scripts/verify_tutorial.py
python3 Scripts/build_starter_project.py --check

if command -v xcrun >/dev/null 2>&1; then
    (
        cd HandConstellation/HandConstellation.docc
        # Highlight bases (HL-*) are only diffed against their target, never
        # shown, and removing lines can leave them incomplete, so only the
        # displayed snapshots have to parse.
        for snapshot in C0*.swift; do
            xcrun swiftc -parse "$snapshot" >/dev/null 2>&1 \
                || { echo "snapshot does not parse: $snapshot"; exit 1; }
        done
        echo "all displayed snapshots parse as Swift"
    )
    if $builds; then
        python3 Scripts/verify_snapshot_builds.py
    fi
fi
