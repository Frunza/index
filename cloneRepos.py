#!/usr/bin/env python3
"""
Clone all GitHub repositories found in entries.json.

Rules:
- For each entry, look for a link with label "Github" (case-insensitive).
- If no GitHub link exists, skip that entry.
- Clone into a directory named after the repo (the last path segment of the GitHub URL),
  e.g. https://github.com/Frunza/some-repo -> ./some-repo
- If the directory already exists, skip it.
- Run this script with the following command: `python cloneRepos.py`
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse


ENTRIES_FILE = Path("entries.json")
CLONE_ROOT = Path(".")


def loadEntries(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("entries.json must be a JSON array of entries")
    return data


def isGithubLabel(label: str) -> bool:
    return label.strip().lower() == "github"


def extractRepoName(githubUrl: str) -> str:
    """
    Extract repo name from GitHub URL: https://github.com/OWNER/REPO(.git)? -> REPO
    """
    parsed = urlparse(githubUrl)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Not a valid GitHub repo URL: {githubUrl}")
    repo = parts[-1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return repo


def findGithubUrl(entry: Dict[str, Any]) -> str | None:
    links = entry.get("links", [])
    if not isinstance(links, list):
        return None

    for link in links:
        if not isinstance(link, dict):
            continue
        label = str(link.get("label", ""))
        url = str(link.get("url", "")).strip()
        if url and isGithubLabel(label):
            return url
    return None


def cloneRepo(githubUrl: str, targetDir: Path) -> None:
    # Keep it simple: run git directly and stream output to the console.
    subprocess.run(
        ["git", "clone", githubUrl, str(targetDir)],
        check=True,
    )


def main() -> None:
    if not ENTRIES_FILE.exists():
        raise SystemExit(f"Missing {ENTRIES_FILE}")

    entries = loadEntries(ENTRIES_FILE)

    for i, entry in enumerate(entries):
        githubUrl = findGithubUrl(entry)
        if not githubUrl:
            continue

        try:
            repoName = extractRepoName(githubUrl)
        except ValueError as e:
            print(f"[skip] Entry #{i}: {e}")
            continue

        targetDir = CLONE_ROOT / repoName
        if targetDir.exists():
            print(f"[skip] {repoName} (already exists)")
            continue

        print(f"[clone] {githubUrl} -> {targetDir}")
        try:
            cloneRepo(githubUrl, targetDir)
        except subprocess.CalledProcessError as e:
            print(f"[error] Failed to clone {githubUrl}: {e}")


if __name__ == "__main__":
    main()
