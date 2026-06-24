# Security Policy

RepoProof executes code from the repositories it inspects, so security is a first-class concern.

## Reporting a vulnerability

Please report suspected vulnerabilities via
[GitHub Security Advisories](https://github.com/ssamba1/repo-proof/security/advisories/new)
(preferred) or by opening a minimal issue that does **not** include exploit details. We aim to
acknowledge reports within a few days.

## Threat model

RepoProof runs untrusted README quickstart commands. Its defenses:

- **Run on a copy.** Commands execute in a disposable temp copy of the repo, torn down even on
  crash, timeout, or interrupt. The user's working tree is never modified.
- **No shell.** Commands are parsed with `shlex` and run as an argv list — never `shell=True`.
  Pipe-to-shell (`curl … | sh`) and `rm -rf /` are refused.
- **README is data.** Only fenced code blocks are parsed; instructions embedded in prose or HTML
  comments are ignored (prompt-injection resistance).
- **Secret-scrubbed environment.** Child processes receive the environment minus secret-shaped
  variables (`*_TOKEN`, `*_KEY`, `*_SECRET`, `AWS_*`, `GH_*`, `OPENAI*`, …).
- **Hardened Docker.** When Docker is available: `--cap-drop ALL`, `--pids-limit`, `--memory`,
  `--cpus`, `--security-opt no-new-privileges`, non-root user.

## Residual risk

The **subprocess** fallback (used when Docker is unavailable) runs repo code on the host. It is
flagged in every result. For untrusted repositories, prefer running with Docker available, or use
`--mode docker` explicitly.

## Supply chain

This repo has **zero runtime dependencies**. A tracked pre-commit hook (`.githooks/pre-commit`)
blocks credential-shaped content and secret filenames from being committed.
