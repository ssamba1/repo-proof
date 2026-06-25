# Spec: RepoProof — Verified READMEs + Real Demos for Claude Code

> Status: DRAFT — Phase 1 (Specify). Awaiting human review before Plan phase.
> Command prefix: `/proof`. Skills: `proof-verify`, `proof-demo`.

## Objective

A Claude Code skill suite that makes a GitHub repo **genuinely good**, not just
*look complete*. It competes with existing repo-beautify skills (avalonreset/claude-github,
GLINCKER readme-generator) on the one dimension they ignore: **trust**.

Existing tools optimize *appearance of completeness* (file checklist + SEO keyword
stuffing) and ship **unverified** examples plus **AI-generated** banner images. RepoProof
ships the opposite:

- **`proof-verify`** — extract the README quickstart (install + first example), run it in a
  sandbox, assert it actually works, and fix/flag the commands that don't. Guarantees the
  quickstart a stranger copy-pastes will succeed.
- **`proof-demo`** — capture a *real* demo of the project running (terminal GIF for CLIs,
  screenshot for web apps) — an actual artifact, not an AI fantasy banner.

**Users:** OSS maintainers who want a README that provably works and a real demo without
manual effort; and skeptics burned by broken quickstarts and AI-slop banners.

**Why it wins:** A working quickstart + a real demo are what actually drive a reader from
"what is this" to "I'll try it" — the thing that converts to stars. Boilerplate
(LICENSE/CoC/templates) is table stakes Claude Code already generates free; RepoProof bundles
it but does not lead with it.

**Non-goals for v1:** SEO/keyword research, AI banner/avatar generation, doc-code drift CI
guard (deferred to v2), monorepo orchestration, legal/community file generation as a headline
feature.

## Prior Art & Differentiation

The idea is **not original** — the pieces are commoditized. Honest landscape:

| Capability | Existing tools | Gap RepoProof fills |
|---|---|---|
| Run README code in CI | Runme, byexample, cram, tesh, doctest, mdbook test | All need **annotated/structured** blocks or doctest syntax. RepoProof infers the quickstart from **arbitrary prose**, zero config. |
| Report pass/fail of examples | Runme, readme-to-test | They only **report**. RepoProof **auto-fixes** the broken command and re-runs (repair loop). |
| Demo recording | vhs, asciinema, terminalizer, Playwright | All **manual scripting**. RepoProof auto-detects type and captures in the same pass. |
| AI repo beautifier | avalonreset/claude-github, GLINCKER | **Generate, never verify.** Ship unverified commands + AI-slop banners. |
| Sandboxed run+fix of code | Codex, Claude Code themselves | The agent's core loop — but **ad-hoc, hand-driven each time**, not a repeatable packaged pipeline. |

**The unoccupied shape:** zero-config extract → sandbox-run → **auto-fix** → **bundled real demo**,
as a one-command Claude Code skill. No single tool ships that combination.

**Defensibility is thin and we accept it:** any general agent *can be prompted* to do this.
RepoProof's moat is **reliability + DX**, not novelty — "works repeatably on any repo without
prompt-engineering it each time." We compete on execution quality, not a unique idea. This is a
better mousetrap, not a blue ocean — greenlit on that basis.

## Tech Stack

- **Skill format:** Agent Skills open standard — `SKILL.md` + `references/` + `scripts/`,
  installed to `~/.claude/skills/`. Same shape as avalonreset/claude-github.
- **Runtime core:** Python 3.10+ (deterministic logic in `scripts/`, invoked by the skill).
- **Sandbox:** Docker CLI (preferred) or local subprocess fallback (auto-detected).
- **CLI demo capture:** [`vhs`](https://github.com/charmbracelet/vhs) preferred (scriptable,
  deterministic GIF), `asciinema` + `agg` fallback. (Tooling choice — see Open Questions.)
- **Web demo capture:** Playwright (available via the session's Playwright MCP; standalone
  `playwright` Python for the installed product).
- **Installers:** `install.sh` (macOS/Linux), `install.ps1` (Windows). MIT licensed.
- **Languages supported for verify:** Python, Node/JS, Rust, Go.

## Commands

```bash
# Install (public OSS, day 1)
git clone https://github.com/ssamba1/repo-proof.git && cd repo-proof && bash install.sh   # macOS/Linux
git clone https://github.com/ssamba1/repo-proof.git ; cd repo-proof ; .\install.ps1        # Windows

# Use (inside Claude Code, run from target repo root)
/proof verify        # extract quickstart → run in sandbox → assert → fix/flag → report
/proof demo          # detect project type → run → capture real GIF/screenshot → embed in README
/proof verify --no-fix      # report only, do not rewrite README
/proof demo --web http://localhost:3000   # force web-app capture against a running URL

# Dev (in repo-proof itself)
Test:   pytest -q
Lint:   ruff check . && ruff format --check .
Types:  (optional) pyright scripts/
Run sandbox manually:  python scripts/sandbox.py --repo <path> --cmd "..." --mode auto
```

## Project Structure

```
repo-proof/
  SPEC.md                      → this file (living source of truth)
  README.md                    → product README (dogfooded by proof-verify)
  LICENSE                      → MIT
  install.sh / install.ps1     → installers (write only inside ~/.claude/)
  proof/                       → orchestrator skill (routing + intent capture)
    SKILL.md
    references/                → per-language quickstart conventions, sandbox notes
    scripts/                   → deterministic Python core (the real logic)
      extract.py               → parse README → ordered (install, example) command list
      sandbox.py               → run a command list; mode = docker | subprocess | auto
      verify.py                → orchestrate extract→sandbox→assert→diff; emit report
      fix.py                   → propose corrected commands for failures
      demo_cli.py              → vhs/asciinema capture → GIF
      demo_web.py              → playwright capture → PNG
      detect.py                → classify repo (lang, CLI vs web, entrypoint)
  skills/
    proof-verify/SKILL.md
    proof-demo/SKILL.md
  fixtures/                    → sample mini-repos for tests
    py-working/  py-broken/
    node-working/ node-broken/
    rust-working/ rust-broken/
    go-working/  go-broken/
  tests/                       → pytest: unit (extract/detect/fix) + integration (sandbox)
```

## Code Style

Python, typed, small pure functions, ruff-formatted. Subprocess **always** list-args with an
explicit timeout — never `shell=True` on a string derived from a repo's README.

```python
# scripts/sandbox.py
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RunResult:
    cmd: list[str]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool

def run_step(cmd: list[str], cwd: Path, timeout_s: int = 300) -> RunResult:
    """Run one quickstart step. Never shell=True; repo-derived input is untrusted."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=timeout_s, check=False,
        )
        return RunResult(cmd, p.returncode, p.stdout, p.stderr, timed_out=False)
    except subprocess.TimeoutExpired as e:
        return RunResult(cmd, 124, e.stdout or "", e.stderr or "", timed_out=True)
```

Conventions: `snake_case` functions/files, frozen dataclasses for results, no bare `except`,
all external commands time-boxed, all paths via `pathlib.Path`.

## Testing Strategy

- **Framework:** pytest. Tests live in `tests/`, fixtures in `fixtures/`.
- **Fixtures:** 8 mini-repos = 4 languages × {working, broken}. "Broken" = a README whose
  quickstart command is wrong (typo'd package, missing flag, wrong entrypoint).
- **Unit:** `extract.py` (README → command list across formats), `detect.py` (lang/type),
  `fix.py` (broken cmd → corrected cmd) — fast, no sandbox.
- **Integration:** run `sandbox.py` on every fixture. Assert: `*-working` → exit 0 verified;
  `*-broken` → failure detected, and (`--fix`) a corrected command re-runs to exit 0.
- **Both sandbox modes:** subprocess path always; Docker path gated behind a
  `docker --version` check (`pytest.mark.skipif` when absent) so CI without Docker still passes.
- **Coverage target:** ≥80% on `proof/scripts/`. Self-test: run `/proof verify` on RepoProof's
  own README — it must pass (dogfood gate, mirrors skill-doctor's `test_dogfood.py`).

## Boundaries

**Always:**
- Run untrusted repo code only inside the sandbox (Docker if present), with timeouts.
- Subprocess via list-args; never `shell=True` on repo-derived strings.
- Run `pytest` + `ruff` before any commit.
- Demos must be **real captures** of the project running — never fabricated or AI-generated.

**Ask first (human/user consent):**
- Subprocess fallback when Docker is absent (warn: "about to run THIS repo's code on your host").
- Writing/rewriting files in the *target* repo (README edits, committing demo assets).
- Adding any runtime dependency or any network call from a skill.
- Pushing commits or opening PRs in the target repo.

**Never:**
- `shell=True` on README-derived input; pipe-to-shell installers.
- Run untrusted code on the host without explicit consent + printed warning.
- Commit secrets; store credentials in plaintext (a noted flaw in avalonreset's installer).
- Keyword-stuff descriptions/topics for SEO gaming.
- Fabricate a demo or claim a quickstart "passes" without a real exit-0 run.

## Success Criteria

Concrete, testable — "done" for v1 means all of:

1. `/proof verify` on a repo with a broken quickstart **detects** the failure, **rewrites** the
   command, and **re-runs to exit 0** — proven on all 4 `*-broken` fixtures.
2. `/proof verify` on all 4 `*-working` fixtures passes without edits.
3. `/proof demo` produces a **real artifact**: a `.gif` for a CLI fixture, a `.png` for a web
   fixture, written to `docs/` (or `.proof/`) and embedded in the README.
4. Sandbox runs in Docker when available and falls back to subprocess **with a printed warning**
   when not.
5. `pytest -q` green, `ruff check` clean, ≥80% coverage on `scripts/`, dogfood gate passes.
6. `install.sh` and `install.ps1` write only inside `~/.claude/`, store no plaintext secrets,
   and use no `curl|bash`. Verified by reading the scripts.
7. README documents exactly what data (if any) leaves the machine. Target: **nothing** in v1
   (all-local; no DataForSEO/KIE.ai equivalents).

## Open Questions

1. **CLI demo tooling:** `vhs` (clean, scriptable, needs install) vs `asciinema`+`agg` (common,
   heavier GIF). Pick one as primary for v1? — *recommend `vhs`.*
2. **Quickstarts needing external state** (a database, an API key, a running service): out of
   scope for v1 (report "needs services, skipped") or attempt with docker-compose detection?
   — *recommend: detect & skip-with-clear-report in v1.*
3. **Where do demo assets live** in the target repo — `docs/`, `.proof/`, or repo root? — affects
   README embed paths. *Recommend `docs/`.*
4. **Project/repo name + command prefix:** confirm `RepoProof` / `/proof`. Alternatives: `proofkit`,
   `truerepo`.
5. **Distribution beyond Claude Code:** avalonreset ships Codex/Gemini installers too. v1 = Claude
   Code only? *Recommend yes; port later.* — **Done (v1.1):** `install-gemini.sh`/`.ps1` and
   `install-codex.sh`/`.ps1` ship the package + native custom commands, scoped to each tool's home.
```
