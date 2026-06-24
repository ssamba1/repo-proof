"""Extract the quickstart (install + first run command) from a README.

Security posture: the README is *untrusted data*, never instructions. We only ever look at
fenced code blocks, shell-parse each line into an argv with shlex (never `shell=True`), and
ignore prose, HTML comments, and anything that is not inside a shell-flavored code fence.

Quality posture (informed by tools/benchmark.py against real repos): real READMEs list many
shell lines — multiple install methods (`brew`, `apt`, `sudo port install`, `mise use`, …),
dev scripts, and prose inside code fences. So we (a) classify a broad set of package-manager
invocations as INSTALL so they are not mistaken for the runnable example, (b) split compound
`a && b` lines, (c) skip setup-only commands like `cd`/`export`, and (d) reject lines that are
really prose ("macOS or Linux") rather than a command.
"""

from __future__ import annotations

import re
import shlex

from .models import Command, StepKind

# Headings under which a quickstart is likely to live, best first.
_HEADING_PRIORITY = (
    "quick start",
    "quickstart",
    "getting started",
    "installation",
    "install",
    "usage",
    "running",
    "run",
    "example",
)

_SHELL_LANGS = {"", "bash", "sh", "shell", "console", "zsh", "text", "shellsession"}

_PROMPT_PREFIXES = ("$ ", "# ", "> ", ">>> ", "PS> ", "C:\\> ")

# Placeholder shapes that mean "the user must fill this in" — running as-is is a false failure.
_PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^>]+>"),  # <your-key>
    re.compile(r"\bYOUR[_-][A-Z0-9_]+", re.IGNORECASE),  # YOUR_API_KEY
    re.compile(r"\bpath/to/", re.IGNORECASE),
    re.compile(r"\bexample\.com\b", re.IGNORECASE),
    re.compile(r"\{\{[^}]+\}\}"),  # {{template}}
    re.compile(r"\$\{[A-Z_]+\}"),  # ${ENV_VAR}
    re.compile(r"\bxx+\b", re.IGNORECASE),  # xxxx
)

# Constructs we refuse to execute regardless of where they appear.
_DANGEROUS = re.compile(r"(\|\s*(sudo\s+)?(ba)?sh)|(\brm\s+-rf\s+/)|(\bcurl\b.*\|)|(\bwget\b.*\|)")

# Privilege wrappers stripped before classification.
_SUDO = {"sudo", "doas"}

# Setup-only commands that are never the demonstrable "run" of a project (git clones, shell
# bookkeeping). git in particular shows up as `git clone …` install instructions.
_RUN_SKIP = {"cd", "export", "set", "source", ".", ":", "pushd", "popd", "unset", "git"}

# System package managers — in a README these only ever install, whatever flag syntax they use
# (`pacman -S`, `apt install`, `brew install`, `port install`, …).
_PURE_PM = {
    "apt", "apt-get", "brew", "port", "pacman", "dnf", "yum", "zypper",
    "snap", "scoop", "choco", "winget", "nix-env", "emerge", "xbps-install",
}  # fmt: skip

# Headings whose code blocks are deprioritized — dev/build instructions are not the user quickstart.
_DEPRIORITIZE = ("develop", "contribut", "from source", "building", "hacking", "testing")

# Package managers / install tools. A line headed by one of these with an install-ish verb is
# treated as INSTALL, not as the runnable example.
_INSTALL_HEADS = {
    "pip", "pip3", "pipx", "uv", "uvx", "poetry", "conda", "mamba",
    "npm", "yarn", "pnpm", "bun",
    "cargo", "go", "gem", "bundle", "composer",
    "apt", "apt-get", "brew", "port", "snap", "scoop", "choco", "winget",
    "dnf", "yum", "pacman", "zypper", "nix-env", "mise", "asdf", "make",
}  # fmt: skip
_INSTALL_VERBS = {"install", "add", "sync", "build", "ci", "get", "fetch", "use", "global", "i"}

_COMPOUND = re.compile(r"\s*(?:&&|\|\||;)\s*")
_PROG_RE = re.compile(r"^[a-z][\w.+-]*$")
# Lowercase connectives that betray a prose line masquerading as a command.
_STOPWORDS = {"or", "and", "the", "a", "an", "with", "for", "to", "is", "are", "on", "in", "of"}


class _Block:
    __slots__ = ("lang", "lines", "start_line", "heading")

    def __init__(self, lang: str, lines: list[tuple[int, str]], heading: str) -> None:
        self.lang = lang
        self.lines = lines  # (line_no, text)
        self.start_line = lines[0][0] if lines else 0
        self.heading = heading


def _iter_blocks(readme: str) -> list[_Block]:
    """Parse fenced code blocks, tracking the most recent heading above each."""
    blocks: list[_Block] = []
    heading = ""
    in_fence = False
    fence_lang = ""
    buf: list[tuple[int, str]] = []
    for i, line in enumerate(readme.splitlines(), start=1):
        stripped = line.strip()
        fence = re.match(r"^(```+|~~~+)\s*([A-Za-z0-9+-]*)", stripped)
        if fence and not in_fence:
            in_fence = True
            fence_lang = fence.group(2).lower()
            buf = []
            continue
        if in_fence and re.match(r"^(```+|~~~+)\s*$", stripped):
            in_fence = False
            blocks.append(_Block(fence_lang, buf, heading))
            continue
        if in_fence:
            buf.append((i, line))
            continue
        h = re.match(r"^#{1,6}\s+(.*)$", stripped)
        if h:
            heading = h.group(1).strip().lower()
    return blocks


def _strip_prompt(line: str) -> str:
    for p in _PROMPT_PREFIXES:
        if line.startswith(p):
            return line[len(p) :]
    return line


def find_placeholders(text: str) -> list[str]:
    found: list[str] = []
    for pat in _PLACEHOLDER_PATTERNS:
        found.extend(m.group(0) for m in pat.finditer(text))
    return found


def _join_continuations(raw_lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Merge shell line-continuations (trailing backslash) into single logical commands."""
    out: list[tuple[int, str]] = []
    pending = ""
    pending_no = 0
    for no, text in raw_lines:
        body = _strip_prompt(text.strip())
        if not body or body.startswith("#"):
            continue
        if not pending:
            pending_no = no
        if body.endswith("\\"):
            pending += body[:-1].rstrip() + " "
        else:
            pending += body
            out.append((pending_no, pending.strip()))
            pending = ""
    if pending:
        out.append((pending_no, pending.strip()))
    return out


def _strip_sudo(argv: list[str]) -> list[str]:
    out = list(argv)
    while out and out[0] in _SUDO:
        out.pop(0)
        while out and out[0].startswith("-"):
            opt = out.pop(0)
            if opt in ("-u", "--user") and out:
                out.pop(0)
    return out


def _is_install(argv: list[str]) -> bool:
    if not argv:
        return False
    # `python -m pip install ...`, `python3 -m pip install ...`, `uv pip install ...`
    if "pip" in argv and "install" in argv:
        return True
    head = argv[0].lower()
    if head in _PURE_PM:
        return True
    return head in _INSTALL_HEADS and any(v in argv[1:4] for v in _INSTALL_VERBS)


def _is_prose(argv: list[str]) -> bool:
    """A line is prose, not a command, if it has no flags, no path-like token, and contains an
    English connective (e.g. 'macOS or Linux', 'macOS (with MacPorts)')."""
    cleaned = [t.strip("()[]{}.,:;\"'") for t in argv]
    has_flag = any(t.startswith("-") and len(t) > 1 for t in argv)
    has_path = any("/" in t or "." in t for t in argv)
    has_stopword = any(t.lower() in _STOPWORDS for t in cleaned)
    return has_stopword and not has_flag and not has_path


def _is_plausible_program(token: str) -> bool:
    return "/" in token or "." in token or bool(_PROG_RE.match(token))


def _to_command(line_no: int, text: str) -> Command | None:
    if _DANGEROUS.search(text):
        return None
    try:
        raw_argv = shlex.split(text, posix=True)
    except ValueError:
        return None
    argv = _strip_sudo(raw_argv)
    if not argv:
        return None
    if not _is_plausible_program(argv[0]) or _is_prose(argv):
        return None
    placeholders = find_placeholders(text)
    return Command(
        raw=text,
        argv=tuple(argv),
        kind=StepKind.INSTALL if _is_install(argv) else StepKind.RUN,
        source_line=line_no,
        needs_input=bool(placeholders),
        placeholders=tuple(placeholders),
    )


def _block_score(block: _Block) -> int:
    if block.lang not in _SHELL_LANGS:
        return -1
    if any(k in block.heading for k in _DEPRIORITIZE):
        return 0  # dev/build instructions: only used if nothing better exists
    for rank, key in enumerate(_HEADING_PRIORITY):
        if key in block.heading:
            return 100 - rank
    return 1  # shell block under an unrecognized heading still counts, low priority


def extract_quickstart(readme: str) -> list[Command]:
    """Return the ordered quickstart: install step(s) followed by the first run command.

    Empty list means no quickstart could be located (caller maps to EXTRACTION_FAILED).
    """
    blocks = sorted(_iter_blocks(readme), key=_block_score, reverse=True)
    blocks = [b for b in blocks if _block_score(b) >= 0]
    if not blocks:
        return []

    install: list[Command] = []
    run: Command | None = None
    for block in blocks:
        for line_no, text in _join_continuations(block.lines):
            for piece in _COMPOUND.split(text):
                piece = piece.strip()
                if not piece:
                    continue
                cmd = _to_command(line_no, piece)
                if cmd is None:
                    continue
                if cmd.kind is StepKind.INSTALL:
                    if cmd not in install:
                        install.append(cmd)
                elif cmd.argv[0].lower() in _RUN_SKIP:
                    # Setup-only (cd/export/...). Keep it only if it carries a placeholder, so
                    # `export API_KEY=<your-key>` still surfaces as needs_input.
                    if cmd.needs_input and cmd not in install:
                        install.append(cmd)
                elif run is None:
                    run = cmd
        if run is not None:
            break

    commands = list(install)
    if run is not None:
        commands.append(run)
    return commands
