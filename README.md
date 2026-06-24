# RepoProof

**Verified READMEs + real demos for Claude Code.** Other tools make a repo *look* finished —
they generate a LICENSE, stuff keywords into the description, and paste an AI-generated banner.
RepoProof does the opposite: it *proves* your quickstart actually runs, fixes it when the docs
are wrong (and refuses to hide a real bug), and captures a **real** demo of the thing working.

> Everyone else makes your repo look done. RepoProof makes it provably work — and shows it.

## Quickstart

```bash
python -m proof.scripts.cli verify --help
```

That command prints the verifier's usage. To check a real project, run `proof verify` from its
root (see [Usage](#usage)).

## Install

```bash
git clone https://github.com/ssamba1/repo-proof.git
cd repo-proof
bash install.sh        # macOS / Linux
```

On Windows: `./install.ps1`. The installer copies the skill into `~/.claude/skills/` and writes
nothing else — no `curl | bash`, no credentials, no telemetry.

## What it does

| Command | What happens |
|---------|--------------|
| `/proof verify` | Reads the README quickstart, runs it in a disposable sandbox, and reports whether it actually works. If a command is wrong because the *docs* are wrong (a typo'd filename), it proposes the fix and re-runs to confirm. If the *code* is broken, it says so and never rewrites the README to hide it. |
| `/proof demo` | Captures a real demo: a terminal GIF (via `vhs`) for a CLI, or a screenshot (via Playwright) for a web app. Falls back to a real text transcript when no recorder is installed — never a fabricated image. |

### The integrity rule

A failing quickstart has two very different causes, and RepoProof keeps them apart:

- **Documentation error** (the README says `python man.py`, the file is `main.py`) → corrected and
  re-verified, reported as `fixed`.
- **Real code bug** (the command is right, the program crashes) → reported as `real_code_bug`,
  **never** masked by weakening the example or editing the docs.

This is the whole point. A tool that quietly rewrites READMEs to make broken projects look green is
the problem, not the solution.

## Usage

There are three ways to run it; pick whichever fits.

**1. Inside Claude Code (recommended)** — after `install.sh`, just ask:

```
/proof verify
/proof demo
```

**2. Direct, no install** — from a clone of this repo, target any other repo by path:

```bash
python -m proof.scripts.cli verify path/to/repo
python -m proof.scripts.cli demo path/to/repo
```

**3. From the installed skill** — works from any directory:

```bash
python "$HOME/.claude/skills/proof/run.py" verify path/to/repo   # %USERPROFILE% on Windows
```

Common flags (any of the forms above):

```bash
--json            # machine-readable report + CI exit code
--write           # apply a proposed doc fix in place (off by default)
--mode subprocess # force subprocess sandbox (default: auto-detect Docker)
--web http://localhost:3000   # demo: screenshot a running web app
```

> Want a bare `proof` command on your PATH? Install the package: `pip install .` (or
> `pipx install .`). `install.sh` deliberately does **not** touch your Python environment.

### Exit codes (for CI)

| Code | Meaning |
|------|---------|
| 0 | `verified`, `fixed`, or legitimately skipped (needs input/services, no sandbox) |
| 1 | `unfixable_doc_error` |
| 2 | `real_code_bug` |
| 3 | `extraction_failed` (no quickstart found) |
| 4 | `timeout` |

## Safety

- Quickstarts run in a **disposable copy** of the repo (Docker when available, otherwise a
  consent-flagged subprocess), torn down even on crash or timeout. Your working tree is never
  touched and never polluted.
- The child process gets a **scrubbed environment** — secrets in your shell (`*_TOKEN`, `*_KEY`,
  AWS/GH/OpenAI vars) are not handed to untrusted code.
- READMEs are treated as **data, never instructions**. Only fenced code blocks are parsed, and
  pipe-to-shell constructs are refused.

## Development

```bash
python -m pip install ruff pytest
python -m ruff check .
python -m pytest -q
```

Tests cover four ecosystems (Python, Node, Rust, Go). Integration tests skip cleanly when a
toolchain is absent; the dogfood test verifies this very README.

## License

MIT — see [LICENSE](LICENSE). Not affiliated with Anthropic or GitHub, Inc.
