"""Classify a repo: language, and whether it is a CLI, a web app, or a library.

Marker-file based and deliberately conservative — when unsure we say so rather than
guess, so downstream steps can skip cleanly instead of running the wrong thing.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Lang, ProjectKind

_WEB_DEP_MARKERS = (
    "flask",
    "django",
    "fastapi",
    "starlette",
    "uvicorn",
    "express",
    "next",
    "vite",
    "react-dom",
    "@angular/core",
    "vue",
    "svelte",
    "actix-web",
    "axum",
    "rocket",
)


def detect_lang(repo: Path) -> Lang:
    if (repo / "Cargo.toml").is_file():
        return Lang.RUST
    if (repo / "go.mod").is_file():
        return Lang.GO
    if (repo / "package.json").is_file():
        return Lang.NODE
    if any((repo / f).is_file() for f in ("pyproject.toml", "setup.py", "requirements.txt")):
        return Lang.PYTHON
    # Fall back to file-extension census.
    counts: dict[Lang, int] = {Lang.PYTHON: 0, Lang.NODE: 0, Lang.RUST: 0, Lang.GO: 0}
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf == ".py":
            counts[Lang.PYTHON] += 1
        elif suf in (".js", ".ts", ".mjs"):
            counts[Lang.NODE] += 1
        elif suf == ".rs":
            counts[Lang.RUST] += 1
        elif suf == ".go":
            counts[Lang.GO] += 1
    best = max(counts, key=lambda k: counts[k])
    return best if counts[best] > 0 else Lang.UNKNOWN


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def detect_kind(repo: Path, lang: Lang) -> ProjectKind:
    blob = ""
    if lang == Lang.NODE and (repo / "package.json").is_file():
        try:
            pkg = json.loads(_read_text(repo / "package.json"))
        except (json.JSONDecodeError, ValueError):
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        blob = " ".join(deps).lower()
        scripts = pkg.get("scripts", {})
        has_server_script = any(k in scripts for k in ("start", "dev", "serve"))
        if has_server_script and any(m in blob for m in _WEB_DEP_MARKERS):
            return ProjectKind.WEB
        if "bin" in pkg:
            return ProjectKind.CLI
    elif lang == Lang.PYTHON:
        for f in ("pyproject.toml", "requirements.txt", "setup.py"):
            blob += _read_text(repo / f).lower()
    elif lang == Lang.RUST:
        blob = _read_text(repo / "Cargo.toml").lower()
    elif lang == Lang.GO:
        blob = _read_text(repo / "go.mod").lower()

    if any(m in blob for m in _WEB_DEP_MARKERS):
        return ProjectKind.WEB
    # A runnable entrypoint suggests CLI; otherwise treat as library.
    entry_names = ("main.py", "__main__.py", "app.py", "cli.py", "main.rs", "main.go", "index.js")
    if any((repo / e).is_file() for e in entry_names) or (repo / "src" / "main.rs").is_file():
        return ProjectKind.CLI
    if lang == Lang.UNKNOWN:
        return ProjectKind.UNKNOWN
    return ProjectKind.LIBRARY
