# Sandbox safety model

How RepoProof runs untrusted repo code without endangering the host.

## Isolation
- The repo is **copied** to a disposable temp directory (excluding `.git`, `node_modules`,
  `target`, `.venv`, `__pycache__`, `*.pyc`, `.proof`). Commands run in the copy, so the user's
  working tree is never modified or polluted.
- The temp directory is removed in a `finally` block — on success, failure, timeout, or interrupt.

## Modes
- **docker** (preferred when `docker` is on PATH): runs in `python:3.12-slim` / `node:20-slim` /
  `rust:1-slim` / `golang:1-bookworm` with `--rm --user 1000:1000 --memory 2g --cpus 2
  --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges`.
- **subprocess** (fallback): runs on the host. Because untrusted code executes on the host, this
  mode is flagged in every result and should be used with the user's awareness.
- **auto**: Docker if available, else subprocess.

## Environment scrub
The child process receives the host environment **minus secret-shaped variables** — names
matching `TOKEN`, `SECRET`, `PASSWORD`, `API_KEY`, `ACCESS_KEY`, `PRIVATE_KEY`, `SESSION`,
`COOKIE`, `AUTH`, or prefixed with provider names (`AWS_`, `GH_`, `GITHUB_`, `OPENAI`,
`ANTHROPIC`, `NPM_`, `AZURE_`, `GCP_`, `GOOGLE_`, ...). A denylist is used rather than an
allowlist so native toolchains keep the build variables they need (e.g. the MSVC linker's
`LIB`/`INCLUDE`) while credentials are still withheld.

## Command parsing
Commands come only from fenced code blocks and are parsed into an argv with `shlex` — never run
through a shell. Pipe-to-shell constructs (`curl ... | sh`) and `rm -rf /` are refused outright.
