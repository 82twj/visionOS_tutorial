#!/bin/bash
# Runs the tests that need the visionOS Simulator.
#
#   Scripts/run-simulator-tests.sh             the app's tests, including the coordinator
#                                              script in ImmersiveCoordinatorTests
#   Scripts/run-simulator-tests.sh --starter   the starter project's tests as a reader has
#                                              them at the end of Chapter 3
#
# DESTINATION overrides the simulator, for example
#   DESTINATION='platform=visionOS Simulator,name=Apple Vision Pro,OS=27.0'
set -euo pipefail

cd "$(dirname "$0")/.."

destination="${DESTINATION:-platform=visionOS Simulator,name=Apple Vision Pro}"
derived_data="${DERIVED_DATA:-$PWD/.build/simulator-tests}"
project="HandConstellation.xcodeproj"

case "${1:-}" in
    "")
        ;;
    --starter)
        export_root="$(mktemp -d)"
        trap 'rm -rf "$export_root"' EXIT
        python3 Scripts/build_starter_project.py --export "$export_root/HandConstellation" --chapter 3
        project="$export_root/HandConstellation/HandConstellation.xcodeproj"
        derived_data="$derived_data-starter"
        ;;
    *)
        echo "usage: $0 [--starter]" >&2
        exit 2
        ;;
esac

xcodebuild test \
    -project "$project" \
    -scheme HandConstellation \
    -destination "$destination" \
    -derivedDataPath "$derived_data" \
    -parallel-testing-enabled NO \
    CODE_SIGNING_ALLOWED=NO
