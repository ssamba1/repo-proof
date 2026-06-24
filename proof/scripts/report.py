"""Render a VerifyReport as human markdown or machine JSON, and apply README edits.

README edits are *opt-in* (`--write`). By default verify proposes a diff and changes
nothing on disk — rewriting someone's README is high-trust and must be a deliberate act.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import GOOD_OUTCOMES, Outcome, VerifyReport

_EMOJI = {
    Outcome.VERIFIED: "✅",
    Outcome.FIXED: "🔧",
    Outcome.UNFIXABLE_DOC_ERROR: "⚠️",
    Outcome.REAL_CODE_BUG: "❌",
    Outcome.NEEDS_SERVICES: "⏭️",
    Outcome.NEEDS_INPUT: "⏭️",
    Outcome.EXTRACTION_FAILED: "❓",
    Outcome.SANDBOX_UNAVAILABLE: "🚧",
    Outcome.TIMEOUT: "⏱️",
}

_HEADLINE = {
    Outcome.VERIFIED: "Quickstart verified — runs as written.",
    Outcome.FIXED: "Quickstart fixed — a documentation error was corrected and re-verified.",
    Outcome.UNFIXABLE_DOC_ERROR: "Quickstart fails and no safe fix was found.",
    Outcome.REAL_CODE_BUG: "Quickstart fails because the project's own code is broken.",
    Outcome.NEEDS_SERVICES: "Quickstart needs external services/credentials — skipped.",
    Outcome.NEEDS_INPUT: "Quickstart has placeholders to fill in — skipped.",
    Outcome.EXTRACTION_FAILED: "No quickstart could be located in the README.",
    Outcome.SANDBOX_UNAVAILABLE: "Could not run the quickstart in this environment.",
    Outcome.TIMEOUT: "Quickstart timed out.",
}


def to_markdown(report: VerifyReport) -> str:
    emoji = _EMOJI.get(report.outcome, "•")
    lines = [
        f"# RepoProof — verify {emoji}",
        "",
        f"**Result:** {report.outcome.value} — {_HEADLINE[report.outcome]}",
        f"**Project:** {report.lang.value} / {report.kind.value}",
        "",
    ]
    if report.steps:
        lines.append("## Steps")
        for r in report.steps:
            status = "ok" if r.ok else f"exit {r.exit_code}"
            lines.append(f"- `{r.command.raw}` — {status} ({r.duration_s}s, {r.mode})")
        lines.append("")
    if report.proposed_edits:
        lines.append("## Proposed README edit")
        for old, new in report.proposed_edits:
            lines.append(f"```diff\n- {old}\n+ {new}\n```")
        lines.append("")
    if report.notes:
        lines.append("## Notes")
        lines.extend(f"- {n}" for n in report.notes)
        lines.append("")
    lines.append(f"_exit code: {report.exit_code}_")
    return "\n".join(lines)


def to_json(report: VerifyReport) -> str:
    payload = {
        "repo": report.repo,
        "lang": report.lang.value,
        "kind": report.kind.value,
        "outcome": report.outcome.value,
        "exit_code": report.exit_code,
        "trustworthy": report.outcome in GOOD_OUTCOMES,
        "steps": [
            {
                "command": r.command.raw,
                "exit_code": r.exit_code,
                "ok": r.ok,
                "mode": r.mode,
                "duration_s": r.duration_s,
                "timed_out": r.timed_out,
            }
            for r in report.steps
        ],
        "proposed_edits": [{"old": o, "new": n} for o, n in report.proposed_edits],
        "notes": report.notes,
    }
    return json.dumps(payload, indent=2)


def apply_edits(repo: Path, report: VerifyReport) -> int:
    """Apply proposed README edits in place. Returns the number of lines changed."""
    if not report.proposed_edits:
        return 0
    readme = _find_readme(repo)
    if readme is None:
        return 0
    text = readme.read_text(encoding="utf-8", errors="replace")
    changed = 0
    for old, new in report.proposed_edits:
        if old in text:
            text = text.replace(old, new, 1)
            changed += 1
    if changed:
        readme.write_text(text, encoding="utf-8")
    return changed


def _find_readme(repo: Path) -> Path | None:
    for name in ("README.md", "readme.md", "Readme.md", "README"):
        p = repo / name
        if p.is_file():
            return p
    return None
