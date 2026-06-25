# Changelog

All notable changes to RepoProof are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project aims for semantic versioning.

## [Unreleased]

### Added
- Extraction: mine run commands from **inline prose** (`` `cmd args` `` spans and `$`-prefixed
  lines) under usage/quickstart headings, for READMEs with no fenced quickstart block.
- Service detection (R4): repos that declare backing services (a Docker Compose stack or
  service env-vars in an `.env.example`) are reported `needs_services` and skipped with a clear
  message instead of being run-then-misclassified. Opt in to running anyway with `--run-services`.
- Cross-CLI installers: `install-gemini.sh`/`.ps1` (Gemini CLI custom commands `/proof:verify`,
  `/proof:demo`) and `install-codex.sh`/`.ps1` (Codex CLI prompts `/proof-verify`, `/proof-demo`),
  each scoped to that tool's own config home.
- Web demo: a committed real screenshot (`docs/web-demo.png`) from the `proof demo --web` path,
  plus a `web-demo` fixture and an end-to-end capture test.

### Changed
- Run-command ranking: build/test/bench invocations (`cargo test`, `npm run build`, `make`, …)
  are demerited so a real usage example wins — e.g. ripgrep now extracts `rg …` instead of
  `cargo test --all`. Benchmark honest-read updated (~18/20 handled correctly).
- CI: Ruby is now provisioned, so the Ruby fixture integration tests run instead of being skipped.

## [0.1.0] - Unreleased

### Added
- `proof verify`: extract a README quickstart, run it in a disposable sandbox, and classify the
  result across nine outcomes (verified, fixed, real_code_bug, needs_input, needs_services,
  extraction_failed, sandbox_unavailable, unfixable_doc_error, timeout) with CI-friendly exit codes.
- Integrity guarantee: documentation typos are corrected and re-verified; real code bugs are
  reported and never masked.
- `proof demo`: real CLI demo capture via `vhs` with a real text-transcript fallback, and web
  screenshots via Playwright.
- Sandbox: run-on-copy with guaranteed teardown, Docker (hardened) or subprocess modes, and a
  denylist environment scrub that withholds secrets while keeping native build variables.
- Language support: Python, Node, Rust, Go (detection + extraction); Python/Node/Rust integration-tested.
- Claude Code skills: `proof`, `proof-verify`, `proof-demo`, plus `install.sh` / `install.ps1`.
- Test suite (61 tests) including a dogfood test that verifies this repo's own README.
