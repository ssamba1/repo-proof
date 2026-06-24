# Plan: RepoProof v1

> Status: DRAFT — Phase 2 (Plan). Awaiting human review before Tasks phase.
> Source of truth: `SPEC.md`. This plan implements that spec.

## Components & Dependency Graph

```
C0  skeleton + install.sh/.ps1 + 8 fixtures + MIT          (foundation)
         │
   ┌─────┼───────────────┐
   ▼     ▼               ▼
C1 detect.py        C2 extract.py        C3 sandbox.py      (primitives — parallel)
   │     │               │                    │
   └──┬──┴───────────────┘                    │
      ▼                                        │
C4 verify.py  ◄──────────────────────────── (uses C3)
      │
      ▼
C5 fix.py  (re-runs via C3)
                                  C6 demo_cli.py ◄── C3 + C1   (demo branch — parallel to C4/C5)
                                  C7 demo_web.py ◄── C1
   ┌───────────────────────────────────────────────┐
   ▼                                                 ▼
C8 SKILL.md ×3 (orchestrator, proof-verify, proof-demo)   (wiring — after scripts exist)
   │
   ▼
C9 tests (unit per-component TDD; integration after C4/C5; dogfood gate)
   │
   ▼
C10 README (dogfooded) + docs + install-script security read   (ship)
```

**Component summary:**

| ID | Component | Depends on | Notes |
|----|-----------|-----------|-------|
| C0 | Repo skeleton, installers, fixtures, LICENSE | — | 8 fixtures = 4 langs × {working, broken} |
| C1 | `detect.py` — classify lang, CLI-vs-web, entrypoint | C0 | Pure, fast |
| C2 | `extract.py` — README → ordered command list | C0 | Fuzzy; biggest risk (R1) |
| C3 | `sandbox.py` — run cmd list; docker\|subprocess\|auto | C0 | Security core (R2) |
| C4 | `verify.py` — extract→sandbox→assert→diff→report | C1,C2,C3 | The product's spine |
| C5 | `fix.py` — broken cmd → corrected → re-run | C4,C3 | Repair loop = the differentiator |
| C6 | `demo_cli.py` — vhs capture → GIF | C3,C1 | Skip-with-report if vhs absent |
| C7 | `demo_web.py` — Playwright → PNG | C1 | Needs app boot / `--web URL` (R3) |
| C8 | 3× SKILL.md (orchestrator + 2 skills) | C4,C5,C6,C7 | Routing + intent capture |
| C9 | pytest suite + coverage + dogfood gate | all scripts | TDD throughout, not a final phase |
| C10| README + docs + installer review | C8,C9 | Dogfood: `/proof verify` on own README |

## Build Order (phased, with gates)

**Phase A — Foundation.** Build C0. Repo dir, MIT, `install.sh`/`install.ps1` (write only under
`~/.claude/`), 8 fixture mini-repos (working + broken README each, 4 langs).
→ **Gate A:** `install.sh` copies skill into `~/.claude/skills/`; all 8 fixtures present; installer
read confirms no `curl|bash`, no plaintext-secret writes.

**Phase B — Primitives (parallelizable, TDD each).** C1 detect, C2 extract, C3 sandbox — independent,
good subagent fan-out.
→ **Gate B:** unit tests green for all three; `sandbox.py` runs a hardcoded `echo`/`true` in **both**
docker and subprocess modes (docker test `skipif` no Docker).

**Phase C — Verify pipeline (sequential).** C4 verify, then C5 fix.
→ **Gate C:** integration — all 4 `*-working` fixtures verify exit-0 with no edits; all 4 `*-broken`
fixtures are **detected**, **fixed**, and **re-run to exit 0**.

**Phase D — Demo (parallel to Phase C).** C6 demo_cli, C7 demo_web.
→ **Gate D:** a real `.gif` produced from a CLI fixture; a real `.png` from a web fixture; both embed
in a test README. Absent tooling → graceful skip-with-report, not a crash.

**Phase E — Skill wiring.** C8 — orchestrator `proof/SKILL.md` routes `/proof verify|demo`;
`proof-verify` and `proof-demo` SKILL.md call the scripts.
→ **Gate E:** inside Claude Code, `/proof verify` and `/proof demo` run a fixture end-to-end.

**Phase F — Harden & ship.** Finish C9 (coverage ≥80% on `scripts/`, dogfood gate green) and C10
(README, docs, final installer security read).
→ **Gate F (= v1 done):** all 7 SPEC Success Criteria met. `pytest -q` green, `ruff` clean.

## Parallel vs Sequential

- **Parallel:** Phase B's three primitives; Phase D can overlap Phase C entirely (demo branch only
  needs C3 + C1, not verify/fix).
- **Sequential (hard deps):** A → B → C; C5 strictly after C4; E after scripts exist; F last.
- **Subagent dispatch candidates:** B (3 agents: detect / extract / sandbox) and D (2 agents:
  cli / web). Each is self-contained with its own fixtures + tests — clean fan-out, no shared state.

## Risks & Mitigations

| # | Risk | Mitigation | Residual |
|---|------|-----------|----------|
| R1 | README extraction unreliable across formats | Start with fenced blocks under Install/Usage/Quickstart headings + common command patterns; LLM-assist with deterministic fallback; fixtures cover format variety | Some prose READMEs → graceful "couldn't locate quickstart" report |
| R2 | Untrusted repo code execution | Docker default; subprocess **only** with explicit consent + printed warning; timeouts; never `shell=True` | Subprocess mode still runs code on host (consented) |
| R3 | Demo capture flaky (vhs/headless boot) | Gate behind tool presence; web requires bootable app or `--web URL`; skip-with-report if unavailable | Web auto-boot may slip to manual-URL in v1 |
| R4 | Quickstart needs DB/API key/service | Detect & **skip-with-clear-report** (SPEC open-Q2 decision) | Those repos get verify-skipped, not verified |
| R5 | Cross-OS installer (Windows ps1) | Test both; dogfood `install.ps1` on the dev's Windows box | — |
| R6 | Robustness beyond minimal fixtures | v1 scope = 8 fixtures + 2–3 real repos; document limits | Real-world long tail deferred to v2 |
| R7 | "Any agent can do this" (thin moat) | Out of plan scope — addressed by reliability/DX positioning in SPEC | Strategic, not technical |

## Verification Checkpoints

Gates A–F above are the checkpoints. No phase advances until its gate passes. Each script lands
with its tests (TDD per `test-driven-development`). The dogfood gate (`/proof verify` on RepoProof's
own README, mirroring skill-doctor's `test_dogfood.py`) is the final acceptance signal.

## Open Items Carried From Spec

Plan assumes the recommended answers to SPEC Open Questions (vhs; detect-&-skip services; assets in
`docs/`; name RepoProof/`/proof`; Claude Code only). If any flips, the affected component changes:
- vhs → asciinema flips **C6** only.
- services attempt → adds a docker-compose detector to **C2/C4**.
- assets location flips embed paths in **C6/C7/C8**.
