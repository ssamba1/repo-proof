"""Shared types and the failure taxonomy.

The `Outcome` enum is the contract between every component and the report/exit-code
layer. The most important values are `REAL_CODE_BUG` (the repo's own code is broken —
we report it, we never paper over it) versus `FIXED` (a doc-level error we corrected
and re-ran to success). Keeping these distinct is what stops RepoProof from lying.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Lang(str, Enum):
    PYTHON = "python"
    NODE = "node"
    RUST = "rust"
    GO = "go"
    UNKNOWN = "unknown"


class ProjectKind(str, Enum):
    CLI = "cli"
    WEB = "web"
    LIBRARY = "library"
    UNKNOWN = "unknown"


class StepKind(str, Enum):
    INSTALL = "install"
    RUN = "run"


class Outcome(str, Enum):
    """Every terminal state `verify` can reach. Mapped to exit codes in EXIT_CODES."""

    VERIFIED = "verified"  # ran as written, exit 0, no edits needed
    FIXED = "fixed"  # doc-level error corrected, re-ran to exit 0
    UNFIXABLE_DOC_ERROR = "unfixable_doc_error"  # doc looks wrong, no safe correction found
    REAL_CODE_BUG = "real_code_bug"  # failure is in the repo's own code, NOT the doc
    NEEDS_SERVICES = "needs_services"  # needs DB / API key / network service — skipped
    NEEDS_INPUT = "needs_input"  # quickstart has placeholders (<your-key>) — skipped
    EXTRACTION_FAILED = "extraction_failed"  # could not locate a quickstart in the README
    SANDBOX_UNAVAILABLE = "sandbox_unavailable"  # required toolchain (python/node/...) missing
    TIMEOUT = "timeout"  # a step exceeded its time budget


# Exit codes for CI use: 0 = pass or legitimately-skipped, non-zero = a real problem.
EXIT_CODES: dict[Outcome, int] = {
    Outcome.VERIFIED: 0,
    Outcome.FIXED: 0,
    Outcome.NEEDS_SERVICES: 0,
    Outcome.NEEDS_INPUT: 0,
    Outcome.SANDBOX_UNAVAILABLE: 0,
    Outcome.UNFIXABLE_DOC_ERROR: 1,
    Outcome.REAL_CODE_BUG: 2,
    Outcome.EXTRACTION_FAILED: 3,
    Outcome.TIMEOUT: 4,
}

# Outcomes that mean "the quickstart is trustworthy as it will appear to a user".
GOOD_OUTCOMES = frozenset({Outcome.VERIFIED, Outcome.FIXED})


@dataclass(frozen=True)
class Command:
    """One quickstart command, parsed from a README code block."""

    raw: str  # original line as written in the README
    argv: tuple[str, ...]  # shell-parsed argument vector (never run via shell=True)
    kind: StepKind
    source_line: int = 0  # 1-based line number in the README, 0 if unknown
    needs_input: bool = False  # contains placeholders the user must fill in
    placeholders: tuple[str, ...] = ()

    def __str__(self) -> str:
        return self.raw


@dataclass(frozen=True)
class RunResult:
    command: Command
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_s: float
    mode: str  # "docker" | "subprocess"

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


@dataclass(frozen=True)
class Diagnosis:
    """Why a step failed and what (if anything) we may safely do about it."""

    outcome: Outcome
    reason: str
    suggested_fix: Command | None = None  # only ever doc-level; never a code change


@dataclass
class VerifyReport:
    repo: str
    lang: Lang
    kind: ProjectKind
    outcome: Outcome
    steps: list[RunResult] = field(default_factory=list)
    diagnoses: list[Diagnosis] = field(default_factory=list)
    proposed_edits: list[tuple[str, str]] = field(default_factory=list)  # (old, new) README lines
    notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.outcome]


@dataclass(frozen=True)
class DemoResult:
    kind: str  # "gif" | "png" | "text"
    path: str | None
    captured: bool
    tool: str  # "vhs" | "asciinema" | "text-fallback" | "playwright" | "none"
    reason: str = ""
