"""Orchestrate the verify pipeline: detect -> extract -> run -> classify -> (fix + re-run).

The fix step re-runs the *entire* quickstart with the corrected command substituted in
(the sandbox is recreated fresh each run), so a "FIXED" verdict means the corrected
quickstart actually reached exit 0 end to end — not that we hoped it would.
"""

from __future__ import annotations

from pathlib import Path

from . import sandbox
from .classify import classify_failure
from .detect import detect_kind, detect_lang
from .extract import extract_quickstart
from .models import (
    Command,
    Diagnosis,
    Lang,
    Outcome,
    ProjectKind,
    VerifyReport,
)
from .services import detect_services


def _first_failure(results: list) -> int:
    for i, r in enumerate(results):
        if not r.ok:
            return i
    return -1


def verify_repo(
    repo: Path,
    mode: str = "auto",
    timeout_s: int = 300,
    allow_fix: bool = True,
    skip_services: bool = True,
) -> VerifyReport:
    repo = Path(repo)
    lang = detect_lang(repo)
    kind = detect_kind(repo, lang)
    report = VerifyReport(repo=str(repo), lang=lang, kind=kind, outcome=Outcome.VERIFIED)

    if lang is Lang.UNKNOWN:
        report.outcome = Outcome.SANDBOX_UNAVAILABLE
        report.notes.append("Could not determine the project language.")
        return report

    readme = _read_readme(repo)
    if readme is None:
        report.outcome = Outcome.EXTRACTION_FAILED
        report.notes.append("No README found.")
        return report

    commands = extract_quickstart(readme)
    if not commands:
        report.outcome = Outcome.EXTRACTION_FAILED
        report.notes.append("No quickstart code block could be located in the README.")
        return report

    blocked = [c for c in commands if c.needs_input]
    if blocked:
        report.outcome = Outcome.NEEDS_INPUT
        ph = sorted({p for c in blocked for p in c.placeholders})
        report.notes.append(f"Quickstart contains placeholders the user must fill in: {ph}")
        return report

    # R4: if the repo declares backing services (Compose stack / service env vars), running the
    # quickstart in isolation would just fail on a connection error and be misreported. Skip
    # with a clear report instead — unless the caller explicitly opts in to attempting it.
    services = detect_services(repo)
    if services and skip_services:
        report.outcome = Outcome.NEEDS_SERVICES
        report.notes.append(
            f"Quickstart {services}; skipped (re-run with --run-services to attempt anyway)."
        )
        return report

    results = sandbox.run_quickstart(
        commands, repo, lang=lang.value, mode=mode, timeout_s=timeout_s
    )
    report.steps = results
    fail_idx = _first_failure(results)
    if fail_idx == -1:
        report.outcome = Outcome.VERIFIED
        return report

    diagnosis = classify_failure(results[fail_idx], repo)
    report.diagnoses.append(diagnosis)

    if diagnosis.outcome is Outcome.FIXED and diagnosis.suggested_fix is not None and allow_fix:
        return _attempt_fix(repo, commands, fail_idx, diagnosis, report, mode, timeout_s)

    # Any non-fixable diagnosis (real bug, needs services, timeout, ...) is reported as-is.
    report.outcome = diagnosis.outcome
    return report


def _attempt_fix(
    repo: Path,
    commands: list[Command],
    fail_idx: int,
    diagnosis: Diagnosis,
    report: VerifyReport,
    mode: str,
    timeout_s: int,
) -> VerifyReport:
    fixed = diagnosis.suggested_fix
    assert fixed is not None
    patched = list(commands)
    original = patched[fail_idx]
    patched[fail_idx] = fixed
    rerun = sandbox.run_quickstart(
        patched, repo, lang=report.lang.value, mode=mode, timeout_s=timeout_s
    )
    report.steps = rerun
    if _first_failure(rerun) == -1:
        report.outcome = Outcome.FIXED
        report.proposed_edits.append((original.raw, fixed.raw))
        report.notes.append(
            f"Corrected README command on line {original.source_line}: "
            f"`{original.raw}` -> `{fixed.raw}` (verified to exit 0)."
        )
    else:
        # The proposed correction did not actually fix it — do not claim a fix.
        report.outcome = Outcome.UNFIXABLE_DOC_ERROR
        report.notes.append(
            "A candidate correction was found but the re-run still failed; not rewriting."
        )
    return report


def _read_readme(repo: Path) -> str | None:
    for name in ("README.md", "README.rst", "README.txt", "readme.md", "Readme.md", "README"):
        p = repo / name
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return None
    return None


def kind_is_web(kind: ProjectKind) -> bool:
    return kind is ProjectKind.WEB
