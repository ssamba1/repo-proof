"""Classify a failed run: doc error vs the repo's own code being broken.

This module is the integrity core of RepoProof. The whole product thesis is "an
honest, verified quickstart". If we silently rewrote a README to make a genuinely
broken example appear to pass, we would be the very thing we criticize. So a failure
is only ever treated as fixable when it is unambiguously a *documentation* mistake
(a wrong filename/path that clearly exists under another name). Anything that looks
like the program started and then failed in the repo's own code is REAL_CODE_BUG and
is reported, never masked.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path

from .models import Command, Diagnosis, Outcome, RunResult, StepKind

# Interpreter/toolchain missing -> environment problem, not a doc or code problem.
_TOOLCHAIN = re.compile(
    r"(command not found|is not recognized as|no such file or directory: ?'?"
    r"(python|python3|node|cargo|go|npm|yarn|pnpm|rustc)'?)",
    re.IGNORECASE,
)

# Signals that the program started and then failed inside the repo's own code.
_CODE_BUG = re.compile(
    r"(Traceback \(most recent call last\)|"
    r"^\s*File \".*\", line \d+|"  # python frame
    r"error\[E\d+\]|"  # rustc
    r"cannot find (value|function|type)|"  # rustc/go
    r"SyntaxError|TypeError|ReferenceError|"  # node/python
    r"panicked at|"  # rust runtime
    r"AssertionError|"
    r"undefined: |"  # go
    r"\.go:\d+:\d+:)",  # go compile location
    re.MULTILINE,
)

# Needs external state we will not provision.
_NEEDS_SERVICES = re.compile(
    r"(connection refused|could not connect|ECONNREFUSED|"
    r"getaddrinfo|name or service not known|"
    r"missing (api|access) key|unauthorized|401|403|"
    r"environment variable .* (not set|required)|"
    r"could not translate host name)",
    re.IGNORECASE,
)


def _candidate_paths(repo: Path) -> list[str]:
    out: list[str] = []
    for p in repo.rglob("*"):
        if p.is_file() and not any(
            seg in {".git", "node_modules", "target", ".venv", "__pycache__"} for seg in p.parts
        ):
            out.append(p.name)
    return out


def _looks_like_path_arg(token: str) -> bool:
    return token.endswith((".py", ".js", ".mjs", ".ts", ".rs", ".go", ".rb")) or "/" in token


def classify_failure(result: RunResult, repo: Path) -> Diagnosis:
    """Decide what a non-zero run means. Never returns a code-level 'fix'."""
    blob = f"{result.stdout}\n{result.stderr}"

    if result.timed_out:
        return Diagnosis(Outcome.TIMEOUT, "Step exceeded its time budget.")

    if _TOOLCHAIN.search(blob) and not _CODE_BUG.search(blob):
        return Diagnosis(
            Outcome.SANDBOX_UNAVAILABLE,
            "A required interpreter/toolchain is not available in the sandbox.",
        )

    if _NEEDS_SERVICES.search(blob):
        return Diagnosis(
            Outcome.NEEDS_SERVICES,
            "The example needs an external service, credential, or network host; skipped.",
        )

    # Code bug check comes BEFORE the path-typo fix path: if the program clearly entered
    # the repo's own code and blew up, that is never a doc error to be quietly rewritten.
    if _CODE_BUG.search(blob):
        return Diagnosis(
            Outcome.REAL_CODE_BUG,
            "The command ran but the repository's own code failed. Reporting, not rewriting.",
        )

    # Doc-level typo: the run command names a script/path that does not exist, but a
    # very similar filename does. Only then do we propose a correction.
    suggestion = _suggest_path_fix(result.command, repo, blob)
    if suggestion is not None:
        return Diagnosis(
            Outcome.FIXED,
            "The README points at a file that does not exist; a close match was found.",
            suggested_fix=suggestion,
        )

    return Diagnosis(
        Outcome.UNFIXABLE_DOC_ERROR,
        f"The quickstart failed (exit {result.exit_code}) with no safe documentation-level fix.",
    )


def _suggest_path_fix(command: Command, repo: Path, blob: str) -> Command | None:
    if command.kind is not StepKind.RUN:
        return None
    names = _candidate_paths(repo)
    if not names:
        return None
    for idx, token in enumerate(command.argv):
        if not _looks_like_path_arg(token):
            continue
        target = Path(token).name
        if (repo / token).exists() or target in names:
            continue  # this path is fine; not the culprit
        close = difflib.get_close_matches(target, names, n=1, cutoff=0.7)
        if not close:
            continue
        fixed_token = token.replace(target, close[0])
        new_argv = list(command.argv)
        new_argv[idx] = fixed_token
        new_raw = command.raw.replace(token, fixed_token, 1)
        return Command(
            raw=new_raw,
            argv=tuple(new_argv),
            kind=command.kind,
            source_line=command.source_line,
        )
    return None
