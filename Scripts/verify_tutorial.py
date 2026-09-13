#!/usr/bin/env python3
"""Read-only validation for the authored tutorial and an optional DocC archive."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Tuple

from normalize_docc_navigation import LEGACY_ROUTES, chapter_anchor


REFERENCE_PATTERNS = (
    r"file:\s*([A-Za-z0-9._-]+)",
    r"previousFile:\s*([A-Za-z0-9._-]+)",
    r"source:\s*([A-Za-z0-9._-]+)",
)
FINAL_SNAPSHOTS = {
    "AppModel.swift": "C02-T02-AppModel-12.swift",
    "ControlView.swift": "C02-T04-ControlView-14.swift",
    "HandConstellationApp.swift": "C06-T04-HandConstellationApp-03.swift",
    "HandTrackingService.swift": "C04-T05-HandTrackingService-19.swift",
    "ConstellationConfiguration.swift": "C04-T02-Configuration-07.swift",
    "DwellDetector.swift": "C04-T03-DwellDetector-14.swift",
    "ExistingPointConnectionDetector.swift": "C04-T06-ExistingPointConnectionDetector-06.swift",
    "ConstellationModel.swift": "C05-T02-ConstellationModel-14.swift",
    "ConstellationRenderer.swift": "C05-T03-ConstellationRenderer-13.swift",
    "ImmersiveCoordinator.swift": "C06-T03-ImmersiveCoordinator-22.swift",
    "ImmersiveView.swift": "C06-T04-ImmersiveView-04.swift",
}


class Checks:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def source_order(catalog: Path, checks: Checks) -> list[str]:
    overview = catalog / "HandConstellationTutorials.tutorial"
    checks.require(overview.is_file(), f"missing overview: {overview}")
    if not overview.is_file():
        return []
    return re.findall(r'@TutorialReference\(tutorial:\s*"doc:([A-Za-z0-9_-]+)"', overview.read_text(encoding="utf-8"))


def verify_source(root: Path, catalog: Path, checks: Checks) -> Tuple[list[str], dict[str, int]]:
    tutorials = sorted(catalog.glob("*.tutorial"))
    order = source_order(catalog, checks)
    pages = {path.stem for path in tutorials} - {"HandConstellationTutorials"}
    checks.require(bool(order), "overview lists no tutorials")
    checks.require(len(order) == len(set(order)), "overview lists a tutorial more than once")
    checks.require(set(order) == pages, "overview and tutorial files do not contain the same pages")

    referenced: set[str] = set()
    task_counts: dict[str, int] = {}
    for tutorial in tutorials:
        text = tutorial.read_text(encoding="utf-8")
        for pattern in REFERENCE_PATTERNS:
            referenced.update(re.findall(pattern, text))
        if tutorial.stem != "HandConstellationTutorials":
            task_counts[tutorial.stem] = text.count("@Section(")
            checks.require("@Tutorial(" in text, f"{tutorial.name}: missing @Tutorial")
            checks.require("@Section(" in text, f"{tutorial.name}: has no implementation section")
            checks.require("@Steps" in text, f"{tutorial.name}: has no user steps")

    for name in sorted(referenced):
        checks.require((catalog / name).is_file(), f"missing catalog resource: {name}")
    assets = {
        path.name
        for path in catalog.iterdir()
        if path.suffix.lower() in {".swift", ".plist", ".png"}
    }
    orphaned = sorted(assets - referenced)
    checks.require(not orphaned, "unreferenced catalog assets: " + ", ".join(orphaned))

    app = root / "HandConstellation"
    for source, snapshot in FINAL_SNAPSHOTS.items():
        source_path, snapshot_path = app / source, catalog / snapshot
        if not source_path.is_file() or not snapshot_path.is_file():
            checks.require(False, f"missing final snapshot pair: {source} / {snapshot}")
        else:
            checks.require(
                source_path.read_bytes() == snapshot_path.read_bytes(),
                f"final snapshot differs from app source: {snapshot}",
            )
    return order, task_counts


def load_json(path: Path, checks: Checks) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        checks.errors.append(f"invalid render node {path}: {error}")
        return {}


def overview_sequence(overview: dict) -> Tuple[list[str], dict[str, str]]:
    ordered: list[str] = []
    chapter_for: dict[str, str] = {}
    for section in overview.get("sections", []):
        if section.get("kind") == "volume":
            for chapter in section.get("chapters", []):
                for identifier in chapter.get("tutorials", []):
                    ordered.append(identifier)
                    chapter_for[identifier] = chapter.get("name", "")
    return ordered, chapter_for


def resource_values(value: object, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys and isinstance(child, str):
                found.append(child)
            else:
                found.extend(resource_values(child, keys))
    elif isinstance(value, list):
        for child in value:
            found.extend(resource_values(child, keys))
    return found


def verify_archive(
    archive: Path, source_stems: list[str], source_task_counts: dict[str, int], checks: Checks
) -> None:
    overview_path = archive / "data/tutorials/handconstellationtutorials.json"
    overview = load_json(overview_path, checks)
    ordered, chapter_for = overview_sequence(overview)
    overview_paths = [
        path
        for variant in overview.get("variants", [])
        for path in variant.get("paths", [])
        if isinstance(path, str)
    ]
    overview_url = overview_paths[0] if overview_paths else "/tutorials/handconstellationtutorials"
    ordered_stems = [identifier.rsplit("/", 1)[-1] for identifier in ordered]
    checks.require(ordered_stems == source_stems, "built overview order differs from authored overview")
    checks.require(len(ordered) == len(set(ordered)), "built overview repeats a tutorial")

    nodes: dict[str, tuple[Path, dict]] = {}
    for path in sorted((archive / "data/tutorials").rglob("*.json")):
        node = load_json(path, checks)
        identifier = node.get("identifier", {}).get("url")
        if identifier in ordered:
            nodes[identifier] = (path, node)
    missing = [identifier for identifier in ordered if identifier not in nodes]
    checks.require(not missing, "missing built tutorial nodes: " + ", ".join(missing))

    image_root = archive / "images"
    for position, identifier in enumerate(ordered):
        if identifier not in nodes:
            continue
        path, node = nodes[identifier]
        label = path.name
        sections = node.get("sections", [])
        slug = identifier.rsplit("/", 1)[-1].lower()
        route = archive / "tutorials/handconstellation" / slug / "index.html"
        checks.require(route.is_file() and route.stat().st_size > 0, f"{label}: missing HTML route")
        hero = next((item for item in sections if item.get("kind") == "hero"), {})
        checks.require(hero.get("chapter") == chapter_for[identifier], f"{label}: wrong chapter label")
        task_groups = [item for item in sections if item.get("kind") == "tasks"]
        tasks = [task for group in task_groups for task in group.get("tasks", [])]
        checks.require(bool(tasks), f"{label}: no rendered tasks")
        stem = identifier.rsplit("/", 1)[-1]
        checks.require(
            len(tasks) == source_task_counts.get(stem),
            f"{label}: rendered {len(tasks)} of {source_task_counts.get(stem)} authored tasks",
        )
        for task_index, task in enumerate(tasks, 1):
            prefix = f"{label} task {task_index}"
            content_sections = task.get("contentSection")
            checks.require(bool(content_sections), f"{prefix}: empty contentSection")
            steps = task.get("stepsSection")
            checks.require(bool(steps), f"{prefix}: no rendered steps")
            for step_index, step in enumerate(steps or [], 1):
                step_prefix = f"{prefix} step {step_index}"
                checks.require(bool(step.get("content")), f"{step_prefix}: empty instruction")
                for key in ("code", "media", "runtimePreview"):
                    value = step.get(key)
                    if value:
                        checks.require(
                            isinstance(value, str) and value in node.get("references", {}),
                            f"{step_prefix}: unresolved {key} {value}",
                        )
                code = step.get("code")
                if isinstance(code, str) and code in node.get("references", {}):
                    code_ref = node["references"][code]
                    checks.require(
                        code_ref.get("type") == "file" and bool(code_ref.get("content")),
                        f"{step_prefix}: code reference {code} has no rendered content",
                    )

        for resource in resource_values(sections, {"image", "backgroundImage", "media", "runtimePreview"}):
            checks.require(resource in node.get("references", {}), f"{label}: unresolved rendered resource {resource}")

        for ref_id, reference in node.get("references", {}).items():
            if reference.get("type") != "image":
                continue
            variants = reference.get("variants", [])
            checks.require(bool(variants), f"{label}: image {ref_id} has no variants")
            for variant in variants:
                url = variant.get("url", "")
                relative = url.split("/images/", 1)[-1] if "/images/" in url else ""
                checks.require(bool(relative) and (image_root / relative).is_file(), f"{label}: missing rendered image {url}")

        hierarchy_projects = [
            project.get("reference")
            for module in node.get("hierarchy", {}).get("modules", [])
            for project in module.get("projects", [])
        ]
        checks.require(hierarchy_projects == ordered, f"{label}: hierarchy sequence differs from overview")
        expected_chapters: list[Tuple[str, list[str]]] = []
        for tutorial_id in ordered:
            chapter_name = chapter_for[tutorial_id]
            if not expected_chapters or expected_chapters[-1][0] != chapter_name:
                expected_chapters.append((chapter_name, []))
            expected_chapters[-1][1].append(tutorial_id)
        modules = node.get("hierarchy", {}).get("modules", [])
        checks.require(len(modules) == len(expected_chapters), f"{label}: wrong hierarchy chapter count")
        for module, (chapter_name, chapter_tutorials) in zip(modules, expected_chapters):
            module_projects = [project.get("reference") for project in module.get("projects", [])]
            module_reference = node.get("references", {}).get(module.get("reference"), {})
            checks.require(module_projects == chapter_tutorials, f"{label}: wrong tutorials in chapter {chapter_name}")
            checks.require(module_reference.get("title") == chapter_name, f"{label}: wrong hierarchy label for {chapter_name}")
            checks.require(
                module_reference.get("url") == f"{overview_url}#{chapter_anchor(chapter_name)}",
                f"{label}: chapter {chapter_name} does not link to its overview anchor",
            )
        callouts = [item for item in sections if item.get("kind") == "callToAction"]
        if position + 1 < len(ordered):
            actual = callouts[-1].get("action", {}).get("identifier") if callouts else None
            checks.require(actual == ordered[position + 1], f"{label}: Next does not point to the following overview page")
        else:
            checks.require(not callouts, f"{label}: final tutorial unexpectedly has a Next action")

    checks.require((archive / "index.html").is_file(), "archive has no index.html")
    checks.require((archive / "index/index.json").is_file(), "archive has no search index")
    live_slugs = {identifier.rsplit("/", 1)[-1].lower() for identifier in ordered}
    routes_root = archive / "tutorials/handconstellation"
    for old_slug, new_slug in LEGACY_ROUTES.items():
        if old_slug in live_slugs:
            continue
        redirect = routes_root / old_slug / "index.html"
        text = redirect.read_text(encoding="utf-8") if redirect.is_file() else ""
        checks.require(
            f"../{new_slug}/" in text and "location.search+location.hash" in text,
            f"legacy route {old_slug} does not redirect to {new_slug}",
        )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=root / "HandConstellation/HandConstellation.docc")
    parser.add_argument("--archive", type=Path, help="also validate a generated .doccarchive")
    args = parser.parse_args()

    checks = Checks()
    order, task_counts = verify_source(root, args.catalog.resolve(), checks)
    if args.archive:
        verify_archive(args.archive.resolve(), order, task_counts, checks)
    if checks.errors:
        for error in checks.errors:
            print(f"error: {error}", file=sys.stderr)
        raise SystemExit(f"tutorial verification failed with {len(checks.errors)} error(s)")
    archive_note = f" and archive {args.archive}" if args.archive else ""
    print(f"verified {len(order)} authored tutorial pages{archive_note}")


if __name__ == "__main__":
    main()
