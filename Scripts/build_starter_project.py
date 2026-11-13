#!/usr/bin/env python3
"""Builds the tutorial starter project and its downloadable zip.

The starter's Swift files come from the app sources (files the tutorial
provides complete) and from the catalog's first snapshots (files the reader
writes), so the starter always matches the code the tutorial starts from.
The Xcode project, asset catalog and README are committed as they are.

    python3 Scripts/build_starter_project.py             # rewrite files and zip
    python3 Scripts/build_starter_project.py --check     # verify, write nothing
    python3 Scripts/build_starter_project.py --export DIR --chapter 3
                                                         # starter as it is at the end of Chapter 3

The zip is reproducible: sorted entries, a fixed timestamp and fixed
permissions, under a single ``HandConstellation-Starter/`` folder.
"""

from __future__ import annotations

import argparse
import io
import plistlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "HandConstellation"
CATALOG = APP / "HandConstellation.docc"
STARTER = ROOT / "StarterProject" / "HandConstellation"
SOURCES = STARTER / "HandConstellation"
ZIP_PATH = CATALOG / "HandConstellation-Starter.zip"
ZIP_ROOT = "HandConstellation-Starter"
ZIP_DATE = (2026, 1, 1, 0, 0, 0)
EXCLUDED_NAMES = {".DS_Store", "xcuserdata", "build", "DerivedData", ".swiftpm"}
EXCLUDED_SUFFIXES = {".xcuserstate"}

# Starter Swift file -> the file it is copied from.
STARTER_SWIFT = {
    # Provided complete.
    "AppModel.swift": APP / "AppModel.swift",
    "ControlView.swift": APP / "ControlView.swift",
    "ConstellationConfiguration.swift": APP / "ConstellationConfiguration.swift",
    "ConstellationModel.swift": APP / "ConstellationModel.swift",
    "ExistingPointConnectionDetector.swift": APP / "ExistingPointConnectionDetector.swift",
    # Partly provided: WindowGroup only (Chapter 4 adds the ImmersiveSpace).
    "HandConstellationApp.swift": CATALOG / "C02-T03-HandConstellationApp-02.swift",
    # Partly provided: everything except update(position:at:) (Chapter 3).
    "DwellDetector.swift": CATALOG / "C04-T07-DwellDetector-00.swift",
    # `import Foundation` only.
    "HandTrackingService.swift": CATALOG / "C03-T01-HandTrackingService-00.swift",  # Chapter 2
    "ConstellationRenderer.swift": CATALOG / "C05-T01-ConstellationRenderer-00.swift",  # Chapter 3
    "ImmersiveCoordinator.swift": CATALOG / "C06-T01-ImmersiveCoordinator-00.swift",  # Chapter 4
    "ImmersiveView.swift": CATALOG / "C06-T01-ImmersiveView-00.swift",  # Chapter 4
}

# Files the reader has finished at the end of each chapter (cumulative).
CHAPTER_FILES = {
    1: {},  # Chapter 1 adds the hand-tracking usage description to Info.plist.
    2: {"HandTrackingService.swift": CATALOG / "C04-T05-HandTrackingService-19.swift"},
    3: {
        "DwellDetector.swift": CATALOG / "C04-T03-DwellDetector-14.swift",
        "ConstellationRenderer.swift": CATALOG / "C05-T03-ConstellationRenderer-13.swift",
    },
    4: {
        "ImmersiveCoordinator.swift": CATALOG / "C06-T03-ImmersiveCoordinator-22.swift",
        "ImmersiveView.swift": CATALOG / "C06-T04-ImmersiveView-04.swift",
        "HandConstellationApp.swift": CATALOG / "C06-T04-HandConstellationApp-03.swift",
    },
}

# Committed files the starter must contain besides the generated ones.
STATIC_FILES = (
    "README.md",
    "HandConstellation.xcodeproj/project.pbxproj",
    "HandConstellation.xcodeproj/project.xcworkspace/contents.xcworkspacedata",
    "HandConstellation.xcodeproj/xcshareddata/xcschemes/HandConstellation.xcscheme",
    "HandConstellation/Assets.xcassets/Contents.json",
)

HAND_TRACKING_KEY = re.compile(
    r"[ \t]*<key>NSHandsTrackingUsageDescription</key>\n[ \t]*<string>[^<]*</string>\n"
)
PERSONAL_DATA = (
    (re.compile(r"DEVELOPMENT_TEAM\s*="), "a development team"),
    (re.compile(r"Created by "), "a 'Created by' header"),
)


class StarterError(Exception):
    pass


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise StarterError(f"missing source for the starter project: {relative(path)}")
    return path.read_bytes()


def starter_info_plist() -> bytes:
    """The app Info.plist without the key that readers add in Chapter 1."""
    text = read_bytes(APP / "Info.plist").decode("utf-8")
    stripped, count = HAND_TRACKING_KEY.subn("", text)
    if count != 1:
        raise StarterError("HandConstellation/Info.plist has no NSHandsTrackingUsageDescription to remove")
    plistlib.loads(stripped.encode("utf-8"))
    return stripped.encode("utf-8")


def generated_files() -> dict[Path, tuple[bytes, str]]:
    """Starter file -> (expected bytes, where they come from)."""
    files = {
        SOURCES / name: (read_bytes(source), relative(source))
        for name, source in STARTER_SWIFT.items()
    }
    files[SOURCES / "Info.plist"] = (starter_info_plist(), "HandConstellation/Info.plist without NSHandsTrackingUsageDescription")
    return files


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_NAMES for part in path.parts) or path.suffix in EXCLUDED_SUFFIXES


def starter_files() -> list[Path]:
    return sorted(
        path
        for path in STARTER.rglob("*")
        if path.is_file() and not is_excluded(path.relative_to(STARTER))
    )


def build_zip() -> bytes:
    """Zips the starter folder on disk with fixed metadata."""
    files = starter_files()
    directories: set[str] = {""}  # the top HandConstellation-Starter/ folder
    for path in files:
        parent = path.relative_to(STARTER).parent
        while parent != Path("."):
            directories.add(parent.as_posix() + "/")
            parent = parent.parent

    entries: list[tuple[str, Path | None]] = [(name, None) for name in directories]
    entries += [(path.relative_to(STARTER).as_posix(), path) for path in files]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, path in sorted(entries, key=lambda entry: entry[0]):
            info = zipfile.ZipInfo(f"{ZIP_ROOT}/{name}", date_time=ZIP_DATE)
            info.create_system = 3  # Unix, so external_attr carries the permissions.
            if path is None:
                info.external_attr = (0o40755 << 16) | 0x10
                info.compress_type = zipfile.ZIP_STORED
                archive.writestr(info, b"")
            else:
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes(), compresslevel=9)
    return buffer.getvalue()


def zip_manifest(data: bytes) -> dict[str, tuple]:
    """Everything that matters in a zip, independent of the zlib build."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return {
            info.filename: (info.date_time, info.external_attr, info.compress_type, archive.read(info))
            for info in archive.infolist()
        }


def check() -> list[str]:
    """Returns problems with the committed starter project and zip."""
    errors: list[str] = []
    try:
        expected = generated_files()
    except StarterError as error:
        return [str(error)]

    for path, (data, origin) in expected.items():
        if not path.is_file():
            errors.append(f"missing starter file {relative(path)} (expected copy of {origin})")
        elif path.read_bytes() != data:
            errors.append(f"starter file {relative(path)} differs from {origin}")

    unexpected = sorted(
        path for path in SOURCES.glob("*.swift") if path not in expected
    ) if SOURCES.is_dir() else []
    for path in unexpected:
        errors.append(f"unexpected Swift file in the starter project: {relative(path)}")

    for name in STATIC_FILES:
        if not (STARTER / name).is_file():
            errors.append(f"missing starter file {relative(STARTER / name)}")

    for path in starter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, label in PERSONAL_DATA:
            if pattern.search(text):
                errors.append(f"{relative(path)} contains {label}")

    if errors:
        return errors

    if not ZIP_PATH.is_file():
        return [f"missing {relative(ZIP_PATH)}; run python3 Scripts/build_starter_project.py"]
    committed, fresh = zip_manifest(ZIP_PATH.read_bytes()), zip_manifest(build_zip())
    if committed != fresh:
        changed = sorted(
            name
            for name in set(committed) | set(fresh)
            if committed.get(name) != fresh.get(name)
        )
        errors.append(
            f"{relative(ZIP_PATH)} is out of date ({', '.join(changed[:5])}"
            f"{', ...' if len(changed) > 5 else ''}); run python3 Scripts/build_starter_project.py"
        )
    return errors


def write() -> None:
    for path, (data, _) in generated_files().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.is_file() or path.read_bytes() != data:
            path.write_bytes(data)
    data = build_zip()
    if not ZIP_PATH.is_file() or zip_manifest(ZIP_PATH.read_bytes()) != zip_manifest(data):
        ZIP_PATH.write_bytes(data)
    print(f"wrote {relative(SOURCES)} ({len(STARTER_SWIFT)} Swift files) and {relative(ZIP_PATH)}")


def export(destination: Path, chapter: int) -> None:
    """Copies the starter as a reader has it at the end of ``chapter``."""
    if destination.exists():
        raise SystemExit(f"export destination already exists: {destination}")
    shutil.copytree(STARTER, destination, ignore=shutil.ignore_patterns(*EXCLUDED_NAMES, "*.xcuserstate"))
    if chapter >= 1:
        shutil.copyfile(APP / "Info.plist", destination / "HandConstellation/Info.plist")
    for number in range(2, chapter + 1):
        for name, source in CHAPTER_FILES[number].items():
            shutil.copyfile(source, destination / "HandConstellation" / name)
    print(f"exported the end of Chapter {chapter} to {destination}" if chapter else f"exported the starter to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify the starter and zip without writing")
    mode.add_argument("--export", type=Path, metavar="DIR", help="copy the starter to DIR")
    parser.add_argument(
        "--chapter", type=int, choices=sorted(CHAPTER_FILES) + [0], default=0,
        help="with --export: apply the files finished by the end of this chapter",
    )
    args = parser.parse_args()

    if args.check:
        errors = check()
        if errors:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            raise SystemExit(f"starter project check failed with {len(errors)} error(s)")
        print(f"starter project and {ZIP_PATH.name} are up to date")
    elif args.export:
        errors = check()
        if errors:
            raise SystemExit("starter project is out of date: " + "; ".join(errors))
        export(args.export.resolve(), args.chapter)
    else:
        try:
            write()
        except StarterError as error:
            raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
