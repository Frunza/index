#!/usr/bin/env python3
"""
Generate README.md from entries.json.

- Writes a fixed header at the top.
- Uses a preferred section order list.
- Any sections not in that list are appended at the end (alphabetically).
- Keeps entry order as it appears in entries.json (stable).
- Run this script with the following command: `python generate.py`
"""

import json
from pathlib import Path
from typing import Dict, List, Any


HEADER = """# Index

Where possible, repositories run in containers and use `infrastructure as code` and `configuration as code`.
"""

SECTION_ORDER: List[str] = [
    "Docker",
    "GitLab CI",
    "Ansible",
    "Terraform",
    "Kubernetes",
    "Azure",
    "Security",
    "AWS",
    "Tools",
    "Misc",
]

ENTRIES_FILE = Path("entries.json")
OUTPUT_FILE = Path("README.md")


def loadEntries(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("entries.json must be a JSON array of entries")
    return data


def groupBySection(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            raise ValueError(f"Entry #{i} is not an object")
        section = str(e.get("section", "")).strip()
        title = str(e.get("title", "")).strip()
        links = e.get("links", [])

        if not section:
            raise ValueError(f"Entry #{i} missing/empty 'section'")
        if not title:
            raise ValueError(f"Entry #{i} missing/empty 'title'")
        if links is None:
            links = []
        if not isinstance(links, list):
            raise ValueError(f"Entry #{i} 'links' must be a list")

        grouped.setdefault(section, []).append(
            {
                "title": title,
                "links": links,
            }
        )
    return grouped


def formatLinks(links: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        label = str(link.get("label", "")).strip()
        url = str(link.get("url", "")).strip()
        if label and url:
            parts.append(f"[{label}]({url})")
    return " ".join(parts)


def sectionSortKey(section: str) -> tuple:
    # Known sections by explicit order first, then unknown sections last (alphabetical).
    if section in SECTION_ORDER:
        return (0, SECTION_ORDER.index(section), "")
    return (1, 10_000, section.lower())


def generateReadme(entriesPath: Path, outPath: Path) -> None:
    entries = loadEntries(entriesPath)
    grouped = groupBySection(entries)

    sections = sorted(grouped.keys(), key=sectionSortKey)
    lines: List[str] = [HEADER, "\n"]
    for section in sections:
        lines.append(f"## {section}\n\n")
        for entry in grouped[section]:
            title = entry["title"]
            linksLine = formatLinks(entry.get("links", []))

            # Match your original style:
            # - bullet title line
            # - next line contains links
            # - blank line between entries
            lines.append(f"- {title} ")
            if linksLine:
                lines.append(f"{linksLine}\n")
            else:
                lines.append("\n")
            lines.append("\n")

    outPath.write_text("".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    if not ENTRIES_FILE.exists():
        raise SystemExit(f"Missing {ENTRIES_FILE}")
    generateReadme(ENTRIES_FILE, OUTPUT_FILE)


if __name__ == "__main__":
    main()
