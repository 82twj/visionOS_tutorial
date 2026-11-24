#!/usr/bin/env python3
"""Read-only validation for the authored tutorial and an optional DocC archive."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Tuple

import generate_snapshots as snapshots
from build_starter_project import check as check_starter
from normalize_docc_navigation import LEGACY_ROUTES, chapter_anchor


# Directive arguments only: the lookbehind skips Swift signatures in link URLs
# such as `task(name:priority:file:line:_:)`.
REFERENCE_PATTERNS = (
    r"(?<![\w:])file:\s*([A-Za-z0-9._-]+)",
    r"(?<![\w:])previousFile:\s*([A-Za-z0-9._-]+)",
    r"(?<![\w:])source:\s*([A-Za-z0-9._-]+)",
    r"(?<![\w:])projectFiles:\s*([A-Za-z0-9._-]+)",
)
ASSET_SUFFIXES = {".swift", ".plist", ".png", ".jpg", ".gif", ".zip"}
PAGE_KIND = re.compile(r"^@(Tutorial|Article)\b", re.MULTILINE)


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
            kind = PAGE_KIND.search(text)
            if kind is None:
                checks.require(False, f"{tutorial.name}: starts with neither @Tutorial nor @Article")
            elif kind.group(1) == "Tutorial":
                checks.require("@Section(" in text, f"{tutorial.name}: has no implementation section")
                checks.require("@Steps" in text, f"{tutorial.name}: has no user steps")
            else:
                checks.require("@ContentAndMedia" in text, f"{tutorial.name}: article has no content")
                checks.require("@Section(" not in text, f"{tutorial.name}: article has a tutorial section")
            verify_quizzes(tutorial.name, text, checks)

    for name in sorted(referenced):
        checks.require((catalog / name).is_file(), f"missing catalog resource: {name}")
    assets = {
        path.name
        for path in catalog.iterdir()
        if path.suffix.lower() in ASSET_SUFFIXES
    }
    orphaned = sorted(assets - referenced)
    checks.require(not orphaned, "unreferenced catalog assets: " + ", ".join(orphaned))

    # Every snapshot and highlight base is what generate_snapshots.py produces
    # from the app sources, and the last snapshot of each file is the source.
    checks.errors.extend(snapshots.check())

    live_slugs = {stem.lower() for stem in order}
    for old_slug, new_slug in LEGACY_ROUTES.items():
        if old_slug not in live_slugs:
            checks.require(new_slug in live_slugs, f"legacy route {old_slug} points to a missing page {new_slug}")

    checks.errors.extend(check_starter())
    return order, task_counts


def directive_blocks(text: str, directive: str) -> list[tuple[str, str]]:
    """(arguments, body) of every ``@directive(...) { ... }`` block in ``text``."""
    blocks = []
    for match in re.finditer(rf"@{directive}\b(?:\(([^)]*)\))?\s*\{{", text):
        depth, index = 1, match.end()
        while index < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[index], 0)
            index += 1
        blocks.append((match.group(1) or "", text[match.end() : index - 1]))
    return blocks


def verify_quizzes(name: str, text: str, checks: Checks) -> None:
    """Each question has two or three choices, one correct, each with a justification."""
    for number, (_, question) in enumerate(directive_blocks(text, "MultipleChoice"), 1):
        prefix = f"{name} question {number}"
        choices = directive_blocks(question, "Choice")
        correct = [arguments for arguments, _ in choices if re.search(r"isCorrect:\s*true", arguments)]
        checks.require(2 <= len(choices) <= 3, f"{prefix}: has {len(choices)} choices, expected 2 or 3")
        checks.require(len(correct) == 1, f"{prefix}: has {len(correct)} correct choices, expected 1")
        for index, (arguments, body) in enumerate(choices, 1):
            checks.require(
                re.search(r"isCorrect:\s*(true|false)", arguments) is not None,
                f"{prefix} choice {index}: missing isCorrect",
            )
            justifications = directive_blocks(body, "Justification")
            checks.require(
                len(justifications) == 1 and bool(justifications[0][1].strip()),
                f"{prefix} choice {index}: needs one @Justification with text",
            )


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
    archive: Path,
    catalog: Path,
    source_stems: list[str],
    source_task_counts: dict[str, int],
    checks: Checks,
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
        if node.get("kind") == "article":
            body = [item for item in sections if item.get("kind") == "articleBody"]
            checks.require(any(item.get("content") for item in body), f"{label}: article has no rendered body")
        else:
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

    # `@Tutorial(projectFiles:)` copies each project zip into downloads/.
    for project_zip in sorted(catalog.glob("*.zip")):
        copies = list((archive / "downloads").rglob(project_zip.name))
        checks.require(bool(copies), f"archive has no download for {project_zip.name}")
        for copy in copies:
            checks.require(
                copy.read_bytes() == project_zip.read_bytes(),
                f"archive download {copy.relative_to(archive)} differs from the catalog",
            )

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
    catalog = args.catalog.resolve()
    order, task_counts = verify_source(root, catalog, checks)
    if args.archive:
        verify_archive(args.archive.resolve(), catalog, order, task_counts, checks)
    if checks.errors:
        for error in checks.errors:
            print(f"error: {error}", file=sys.stderr)
        raise SystemExit(f"tutorial verification failed with {len(checks.errors)} error(s)")
    archive_note = f" and archive {args.archive}" if args.archive else ""
    print(f"verified {len(order)} authored tutorial pages{archive_note}")


if __name__ == "__main__":
    main()
