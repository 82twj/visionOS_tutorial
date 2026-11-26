#!/usr/bin/env python3
"""Repair DocC tutorial navigation from the rendered overview's canonical order.

DocC can merge chapters whose non-ASCII names sanitize to the same path. That
changes the per-page hierarchy order and therefore the generated Next link. The
overview JSON still contains the correct chapter and tutorial order, so this
script copies that order back into each tutorial render node.

It also gives tutorial sections ASCII anchors so the section menu can scroll
to them, and publishes only the tutorials: the generated module and symbol
pages redirect to the tutorial overview, as does the site root.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Tuple
from urllib.parse import unquote

# Removed tutorial pages -> the live page that now covers their content. The
# starter project replaced the project-setup, app-model, control-window and
# tunable-value pages, and the remaining removed pages were merged into the
# page that follows them.
LEGACY_ROUTES = {
    "creatingthevisionosproject": "readingthestartercode",
    "buildingtheappmodel": "readingthestartercode",
    "buildingthecontrolwindow": "readingthestartercode",
    "creatingtheappmodelfile": "readingthestartercode",
    "renamingcontentviewtocontrolview": "readingthestartercode",
    "collectingtunablevalues": "detectingthedwell",
    "creatingtheinputdetectorfiles": "detectingthedwell",
    "creatingtheconstellationfiles": "renderingpointsandlines",
    "detectingtheclosure": "buildingthecoordinatorlifecycle",
    "storingmultipleconstellations": "buildingthecoordinatorlifecycle",
    "connectingtheinputpipeline": "buildingthecoordinatorlifecycle",
    "creatingtheimmersivefiles": "buildingthecoordinatorlifecycle",
    "creatingthehandtrackingservicefile": "startingthehandtrackingsession",
}


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"cannot read DocC render node {path}: {error}") from error


def tutorial_sequence(overview: dict) -> Tuple[list[dict], list[str]]:
    chapters: list[dict] = []
    ordered: list[str] = []
    for section in overview.get("sections", []):
        if section.get("kind") != "volume":
            continue
        for chapter in section.get("chapters", []):
            tutorials = chapter.get("tutorials", [])
            if tutorials:
                chapters.append(chapter)
                ordered.extend(tutorials)
    if not ordered:
        raise SystemExit("overview has no tutorial sequence")
    if len(ordered) != len(set(ordered)):
        raise SystemExit("overview contains a tutorial more than once")
    return chapters, ordered


def project_entries(render_nodes: dict[str, dict]) -> dict[str, dict]:
    projects: dict[str, dict] = {}
    for node in render_nodes.values():
        hierarchy = node.get("hierarchy", {})
        for module in hierarchy.get("modules", []):
            for project in module.get("projects", []):
                reference = project.get("reference")
                if reference:
                    projects.setdefault(reference, project)
    return projects


def chapter_anchor(name: str) -> str:
    """Return the fragment DocC's overview renderer derives from a title."""
    anchor = re.sub(r"\s+", "-", name.strip())
    anchor = re.sub(r"[^\w-]", "", anchor, flags=re.UNICODE)
    return anchor


def chapter_reference(
    chapter: dict, index: int, overview_id: str, overview_url: str, references: dict
) -> Tuple[str, dict]:
    name = chapter.get("name") or f"Chapter {index + 1}"
    identifier = f"{overview_id}/$normalized-chapter-{index + 1}"
    for candidate, reference in references.items():
        if reference.get("title") == name and reference.get("role") == "article":
            identifier = candidate
            break

    # A collision can make DocC omit a chapter reference. Existing and synthetic
    # references both point to the real title-derived anchor in the overview.
    reference = {
        "abstract": [],
        "identifier": identifier,
        "kind": "article",
        "role": "article",
        "title": name,
        "type": "topic",
        "url": f"{overview_url}#{chapter_anchor(name)}",
    }
    return identifier, reference


def section_anchor_map(nodes: dict[str, dict]) -> dict[str, dict[str, str]]:
    """Maps each tutorial page path to {DocC section anchor: ASCII anchor}.

    DocC writes a section's ``anchor`` as the raw title slug (Korean here) but
    percent-encodes the same fragment in reference URLs. The renderer's section
    menu looks the encoded fragment up with ``getElementById`` and silently
    finds nothing, so selecting a Korean-titled section never scrolls. ASCII
    anchors read the same in both places, in the address bar and on reload.
    """
    anchors: dict[str, dict[str, str]] = {}
    for node in nodes.values():
        paths = [
            path
            for variant in node.get("variants", [])
            for path in variant.get("paths", [])
            if isinstance(path, str)
        ]
        tasks = [
            task
            for section in node.get("sections", [])
            if section.get("kind") == "tasks"
            for task in section.get("tasks", [])
        ]
        if not paths or not tasks:
            continue
        mapping = {
            task["anchor"]: f"section-{number}"
            for number, task in enumerate(tasks, 1)
            if isinstance(task.get("anchor"), str)
        }
        for path in paths:
            anchors[path] = mapping
    return anchors


def apply_section_anchors(value: object, anchors: dict[str, dict[str, str]], page: str) -> None:
    """Rewrites task anchors and every section URL to the ASCII anchors."""
    if isinstance(value, dict):
        if value.get("kind") == "tasks" and isinstance(value.get("tasks"), list):
            mapping = anchors.get(page, {})
            for task in value["tasks"]:
                anchor = task.get("anchor")
                if anchor in mapping:
                    task["anchor"] = mapping[anchor]
        url = value.get("url")
        if isinstance(url, str) and "#" in url:
            path, fragment = url.split("#", 1)
            new_anchor = anchors.get(path, {}).get(unquote(fragment))
            if new_anchor:
                value["url"] = f"{path}#{new_anchor}"
        for child in value.values():
            apply_section_anchors(child, anchors, page)
    elif isinstance(value, list):
        for child in value:
            apply_section_anchors(child, anchors, page)


def redirect_html(target: str, label: str) -> str:
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"refresh\" content=\"0;url={target}\">"
        f"<link rel=\"canonical\" href=\"{target}\"></head>"
        f"<body><a href=\"{target}\">{label}</a>"
        f"<script>location.replace('{target}'+location.search+location.hash)</script>"
        "</body></html>\n"
    )


def remove_reference_documentation(archive: Path, overview_route: str) -> int:
    """Publishes only the tutorials; old documentation URLs go to the overview.

    An app target's docbuild always adds a module page with the app's symbols.
    It is linked from no tutorial page and would show the finished code's API
    to learners, so its render data is dropped and each of its routes, and the
    site root, redirects to the tutorial overview.
    """
    changed = 0
    data_root = archive / "data/documentation"
    if data_root.exists():
        shutil.rmtree(data_root)
        changed += 1
    routes_root = archive / "documentation"
    for page in sorted(routes_root.rglob("index.html")) if routes_root.exists() else []:
        depth = len(page.parent.relative_to(archive).parts)
        html = redirect_html("../" * depth + overview_route, "Continue to the tutorials")
        if page.read_text(encoding="utf-8") != html:
            page.write_text(html, encoding="utf-8")
            changed += 1
    root_page = archive / "index.html"
    html = redirect_html(overview_route, "Continue to the tutorials")
    if not root_page.is_file() or root_page.read_text(encoding="utf-8") != html:
        root_page.write_text(html, encoding="utf-8")
        changed += 1
    return changed


TIME_KEYS = {"estimatedTime", "estimatedTimeInMinutes"}


def strip_estimated_time(value: object) -> None:
    """Removes time estimates so heroes and the overview do not show them.

    DocC requires ``time`` on ``@Article`` and renders it with an English
    label. The pages follow Apple's Develop in Swift tutorials, which show no
    estimate, so the field is dropped from every render node.
    """
    if isinstance(value, dict):
        for key in TIME_KEYS & value.keys():
            del value[key]
        for child in value.values():
            strip_estimated_time(child)
    elif isinstance(value, list):
        for child in value:
            strip_estimated_time(child)


def normalize(archive: Path) -> int:
    overview_path = archive / "data/tutorials/handconstellationtutorials.json"
    overview = load_json(overview_path)
    chapters, ordered = tutorial_sequence(overview)

    data_root = archive / "data/tutorials"
    render_paths = sorted(data_root.rglob("*.json"))
    nodes: dict[str, dict] = {}
    paths_by_id: dict[str, Path] = {}
    for path in render_paths:
        node = load_json(path)
        identifier = node.get("identifier", {}).get("url")
        if identifier in ordered:
            nodes[identifier] = node
            paths_by_id[identifier] = path

    missing = [identifier for identifier in ordered if identifier not in nodes]
    if missing:
        raise SystemExit("missing tutorial render nodes: " + ", ".join(missing))

    projects = project_entries(nodes)
    missing_projects = [identifier for identifier in ordered if identifier not in projects]
    if missing_projects:
        raise SystemExit("missing hierarchy projects: " + ", ".join(missing_projects))

    overview_id = overview.get("identifier", {}).get("url")
    if not overview_id:
        raise SystemExit("overview has no identifier")
    overview_paths = [
        path
        for variant in overview.get("variants", [])
        for path in variant.get("paths", [])
        if isinstance(path, str)
    ]
    overview_url = overview_paths[0] if overview_paths else "/tutorials/handconstellationtutorials"
    anchors = section_anchor_map(nodes)

    changed = 0
    for position, identifier in enumerate(ordered):
        node = nodes[identifier]
        references = node.setdefault("references", {})
        modules = []
        own_chapter_ref = None
        own_chapter_name = None
        for chapter_index, chapter in enumerate(chapters):
            reference_id, chapter_ref = chapter_reference(
                chapter, chapter_index, overview_id, overview_url, references
            )
            references[reference_id] = chapter_ref
            chapter_projects = [projects[item] for item in chapter["tutorials"]]
            modules.append({"reference": reference_id, "projects": chapter_projects})
            if identifier in chapter["tutorials"]:
                own_chapter_ref = reference_id
                own_chapter_name = chapter.get("name")

        hierarchy = node.setdefault("hierarchy", {})
        hierarchy["modules"] = modules
        hierarchy["reference"] = overview_id
        hierarchy["paths"] = [[overview_id, f"{overview_id}/$volume", own_chapter_ref]]

        strip_estimated_time(node)
        page_paths = [
            path
            for variant in node.get("variants", [])
            for path in variant.get("paths", [])
            if isinstance(path, str)
        ]
        apply_section_anchors(node, anchors, page_paths[0] if page_paths else "")

        sections = node.setdefault("sections", [])
        for section in sections:
            if section.get("kind") == "hero":
                section["chapter"] = own_chapter_name
        sections[:] = [section for section in sections if section.get("kind") != "callToAction"]
        if position + 1 < len(ordered):
            next_id = ordered[position + 1]
            next_ref = references.get(next_id)
            if not next_ref:
                raise SystemExit(f"{identifier}: missing reference for next tutorial {next_id}")
            next_is_article = nodes[next_id].get("kind") == "article"
            action_title = "Read article" if next_is_article else "Get started"
            sections.append(
                {
                    "abstract": next_ref.get("abstract", []),
                    "action": {
                        "identifier": next_id,
                        "isActive": True,
                        "overridingTitle": action_title,
                        "overridingTitleInlineContent": [
                            {"text": action_title, "type": "text"}
                        ],
                        "type": "reference",
                    },
                    "featuredEyebrow": "Article" if next_is_article else "Tutorial",
                    "kind": "callToAction",
                    "title": next_ref.get("title", "Next"),
                }
            )

        path = paths_by_id[identifier]
        rendered = json.dumps(node, ensure_ascii=False, separators=(",", ":")) + "\n"
        if path.read_text(encoding="utf-8") != rendered:
            path.write_text(rendered, encoding="utf-8")
            changed += 1

    # Keep the overview's initial action tied to its first listed tutorial.
    strip_estimated_time(overview)
    apply_section_anchors(overview, anchors, overview_url)
    for section in overview.get("sections", []):
        if section.get("kind") == "hero" and isinstance(section.get("action"), dict):
            section["action"]["identifier"] = ordered[0]
    rendered = json.dumps(overview, ensure_ascii=False, separators=(",", ":")) + "\n"
    if overview_path.read_text(encoding="utf-8") != rendered:
        overview_path.write_text(rendered, encoding="utf-8")
        changed += 1

    # Preserve links to removed pages. Relative redirects work with any Pages
    # base path.
    routes_root = archive / "tutorials/handconstellation"
    live_slugs = {identifier.rsplit("/", 1)[-1].lower() for identifier in ordered}
    for old_slug, new_slug in LEGACY_ROUTES.items():
        if old_slug in live_slugs:
            continue
        if new_slug not in live_slugs:
            raise SystemExit(f"legacy redirect target is not in overview: {new_slug}")
        redirect = routes_root / old_slug / "index.html"
        redirect.parent.mkdir(parents=True, exist_ok=True)
        html = redirect_html(f"../{new_slug}/", "Continue to the tutorial")
        if not redirect.is_file() or redirect.read_text(encoding="utf-8") != html:
            redirect.write_text(html, encoding="utf-8")
            changed += 1

    overview_route = overview_url.strip("/") + "/"
    changed += remove_reference_documentation(archive, overview_route)

    print(f"normalized navigation for {len(ordered)} tutorials ({changed} files changed)")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path, help="path to a .doccarchive directory")
    args = parser.parse_args()
    if not args.archive.is_dir():
        raise SystemExit(f"archive does not exist: {args.archive}")
    normalize(args.archive.resolve())


if __name__ == "__main__":
    main()
