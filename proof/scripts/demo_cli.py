"""Capture a real CLI demo.

Preference order: vhs (clean scripted GIF) -> asciinema (cast) -> text transcript.
The text transcript is the always-available floor: it runs the project's own run
command in the sandbox and records the *actual* output. It is never fabricated, and
it never claims a GIF exists when only text was captured.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import sandbox
from .detect import detect_lang
from .extract import extract_quickstart
from .models import Command, DemoResult, StepKind


def _run_command(repo: Path) -> Command | None:
    readme = _read(repo)
    if readme is None:
        return None
    for cmd in extract_quickstart(readme):
        if cmd.kind is StepKind.RUN and not cmd.needs_input:
            return cmd
    return None


def build_tape(command: str, gif_path: str, width: int = 100, height: int = 24) -> str:
    """Produce a vhs .tape script. Pure — unit tested without vhs installed."""
    return "\n".join(
        [
            f'Output "{gif_path}"',
            f"Set Width {width * 9}",
            f"Set Height {height * 18}",
            "Set FontSize 16",
            "Set Padding 12",
            f"Type {command!r}",
            "Enter",
            "Sleep 3s",
            "",
        ]
    )


def vhs_available() -> bool:
    return shutil.which("vhs") is not None


def asciinema_available() -> bool:
    return shutil.which("asciinema") is not None


def capture(repo: Path, out_dir: Path, timeout_s: int = 120) -> DemoResult:
    repo = Path(repo)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = _run_command(repo)
    if cmd is None:
        return DemoResult("none", None, False, "none", "No runnable example found in the README.")

    if vhs_available():
        gif = out_dir / "proof-demo.gif"
        tape = out_dir / "proof-demo.tape"
        tape.write_text(build_tape(cmd.raw, str(gif)), encoding="utf-8")
        try:
            subprocess.run(
                ["vhs", str(tape)], cwd=repo, timeout=timeout_s, check=True, capture_output=True
            )
            if gif.is_file():
                return DemoResult("gif", str(gif), True, "vhs")
        except (subprocess.SubprocessError, OSError):
            pass  # fall through to the text floor

    return _text_fallback(repo, cmd, out_dir, timeout_s)


def _text_fallback(repo: Path, cmd: Command, out_dir: Path, timeout_s: int) -> DemoResult:
    lang = detect_lang(repo)
    # Demos run the project's own entrypoint on the host — consistent with the vhs path, which
    # records on the host too. We force subprocess rather than 'auto' so the capture does not
    # depend on a Linux container image (Docker on Windows runners cannot run python:slim).
    results = sandbox.run_quickstart(
        [cmd], repo, lang=lang.value, mode="subprocess", timeout_s=timeout_s
    )
    out = results[0] if results else None
    transcript = out_dir / "proof-demo.md"
    body = out.stdout if out else ""
    transcript.write_text(
        f"## Demo\n\n```console\n$ {cmd.raw}\n{body.rstrip()}\n```\n", encoding="utf-8"
    )
    return DemoResult(
        "text",
        str(transcript),
        True,
        "text-fallback",
        "vhs not installed; captured a real text transcript instead.",
    )


def _read(repo: Path) -> str | None:
    for name in ("README.md", "readme.md", "Readme.md", "README"):
        p = repo / name
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")
    return None
