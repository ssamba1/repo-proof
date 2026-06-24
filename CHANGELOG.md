# Changelog

All notable changes to RepoProof are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/); this project aims for semantic versioning.

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
