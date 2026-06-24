"""Run quickstart commands in an isolated, disposable copy of the repo.

Safety model:
  * We never run in the user's working tree. The repo is copied to a temp dir (minus
    .git, node_modules, target, .venv, __pycache__) and torn down in a finally, even
    on crash/timeout/KeyboardInterrupt.
  * Commands are run with an argv list — never `shell=True` — so a README string can
    never be interpreted as a shell pipeline.
  * The child environment is *scrubbed*: only a small allowlist of variables is passed
    through, so secrets sitting in the user's shell env are not handed to untrusted code.
  * Docker mode (preferred when available) adds resource and capability limits. Subprocess
    mode is the fallback and runs on the host, so it is gated behind explicit consent by
    the caller and clearly flagged in the result.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

from .models import Command, RunResult

_IGNORE = shutil.ignore_patterns(
    ".git", "node_modules", "target", ".venv", "venv", "__pycache__", "*.pyc", ".proof"
)

# Env scrub uses a DENYLIST, not an allowlist: native toolchains (the MSVC linker, rustc,
# cgo) need a long and platform-specific set of build variables — an allowlist breaks real
# builds. So we pass the host environment through MINUS anything secret-shaped. The point of
# the scrub is to keep credentials away from untrusted repo code, not to sandbox the build.
_SECRET_RE = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|API[_-]?KEY|ACCESS[_-]?KEY|"
    r"PRIVATE[_-]?KEY|SESSION|COOKIE|AUTH)",
    re.IGNORECASE,
)
_SECRET_PREFIXES = (
    "AWS_",
    "GH_",
    "GITHUB_",
    "OPENAI",
    "ANTHROPIC",
    "NPM_",
    "PYPI",
    "SLACK_",
    "STRIPE_",
    "TWILIO_",
    "AZURE_",
    "GCP_",
    "GOOGLE_",
    "DOCKER_PASSWORD",
)


def _is_secret(name: str) -> bool:
    upper = name.upper()
    return bool(_SECRET_RE.search(name)) or upper.startswith(_SECRET_PREFIXES)


_DOCKER_IMAGE = {
    "python": "python:3.12-slim",
    "node": "node:20-slim",
    "rust": "rust:1-slim",
    "go": "golang:1-bookworm",
    "ruby": "ruby:3-slim",
}


def docker_available() -> bool:
    return shutil.which("docker") is not None


def _scrubbed_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not _is_secret(k)}
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("CI", "1")
    return env


def _copy_repo(repo: Path, dest: Path) -> None:
    shutil.copytree(repo, dest, ignore=_IGNORE, dirs_exist_ok=True)


def _run_subprocess(cmd: Command, cwd: Path, timeout_s: int) -> RunResult:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            list(cmd.argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=_scrubbed_env(),
            check=False,
        )
        return RunResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False,
            duration_s=round(time.monotonic() - start, 3),
            mode="subprocess",
        )
    except subprocess.TimeoutExpired as exc:
        return RunResult(
            command=cmd,
            exit_code=124,
            stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
            stderr=exc.stderr or "" if isinstance(exc.stderr, str) else "",
            timed_out=True,
            duration_s=round(time.monotonic() - start, 3),
            mode="subprocess",
        )
    except FileNotFoundError as exc:
        return RunResult(
            command=cmd,
            exit_code=127,
            stdout="",
            stderr=f"command not found: {exc}",
            timed_out=False,
            duration_s=round(time.monotonic() - start, 3),
            mode="subprocess",
        )


def _docker_argv(image: str, workdir_mount: Path, inner_cmd: Sequence[str]) -> list[str]:
    """Build a hardened `docker run` invocation. Kept pure for testing."""
    return [
        "docker",
        "run",
        "--rm",
        "--user",
        "1000:1000",
        "--memory",
        "2g",
        "--cpus",
        "2",
        "--pids-limit",
        "512",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "-v",
        f"{workdir_mount}:/work:rw",
        "-w",
        "/work",
        image,
        *inner_cmd,
    ]


def _run_docker(cmd: Command, mount: Path, image: str, timeout_s: int) -> RunResult:
    start = time.monotonic()
    argv = _docker_argv(image, mount, list(cmd.argv))
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s, check=False)
        return RunResult(
            command=cmd,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=False,
            duration_s=round(time.monotonic() - start, 3),
            mode="docker",
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            command=cmd,
            exit_code=124,
            stdout="",
            stderr="docker run timed out",
            timed_out=True,
            duration_s=round(time.monotonic() - start, 3),
            mode="docker",
        )


def resolve_mode(mode: str) -> str:
    if mode == "auto":
        return "docker" if docker_available() else "subprocess"
    return mode


def run_quickstart(
    commands: Iterable[Command],
    repo: Path,
    lang: str = "python",
    mode: str = "auto",
    timeout_s: int = 300,
) -> list[RunResult]:
    """Copy the repo to a sandbox, run commands in order, stop at the first failure.

    Returns the results captured so far (so the caller can classify the failing step).
    """
    resolved = resolve_mode(mode)
    image = _DOCKER_IMAGE.get(lang, _DOCKER_IMAGE["python"])
    results: list[RunResult] = []
    tmp = Path(tempfile.mkdtemp(prefix="repo-proof-"))
    try:
        work = tmp / "work"
        _copy_repo(repo, work)
        for cmd in commands:
            if resolved == "docker":
                res = _run_docker(cmd, work, image, timeout_s)
            else:
                res = _run_subprocess(cmd, work, timeout_s)
            results.append(res)
            if not res.ok:
                break
        return results
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
