"""Validate the Codex/Gemini packaging templates and installer scripts.

These ship RepoProof to other agent CLIs (SPEC open-Q5). The installers must keep the same
security posture as install.sh: write only inside the tool's own config home, store no
credentials, and never pipe a download into a shell."""

import re
from pathlib import Path

import pytest

from conftest import ROOT

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 has no tomllib
    tomllib = None

# A download piped straight into a shell — the pattern we must never ship.
_PIPE_TO_SHELL = re.compile(r"(curl|wget|Invoke-WebRequest|iwr)\b[^\n]*\|\s*(sudo\s+)?(ba)?sh")

PACKAGING = ROOT / "packaging"


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["verify", "demo"])
def test_gemini_command_template_is_valid(name):
    raw = _read(f"packaging/gemini/commands/proof/{name}.toml")
    assert "@@PROOF_RUN@@" in raw  # placeholder the installer rewrites
    assert "{{args}}" in raw  # Gemini argument injection
    assert f'"@@PROOF_RUN@@" {name}' in raw  # invokes the right subcommand
    if tomllib is not None:
        data = tomllib.loads(raw)
        assert data["description"].strip()
        assert "!{python" in data["prompt"]  # Gemini shell execution syntax


@pytest.mark.parametrize("name", ["proof-verify", "proof-demo"])
def test_codex_prompt_template_is_valid(name):
    raw = _read(f"packaging/codex/prompts/{name}.md")
    assert raw.strip()
    assert "@@PROOF_RUN@@" in raw
    assert "$ARGUMENTS" in raw  # Codex argument substitution
    sub = name.split("-", 1)[1]  # proof-verify -> verify
    assert f'"@@PROOF_RUN@@" {sub}' in raw


@pytest.mark.parametrize(
    ("script", "home_var"),
    [
        ("install-gemini.sh", ".gemini"),
        ("install-codex.sh", ".codex"),
    ],
)
def test_installer_is_safe(script, home_var):
    raw = _read(script)
    # No curl|bash-style remote execution.
    assert not _PIPE_TO_SHELL.search(raw)
    # Writes are scoped to the tool's own home.
    assert home_var in raw
    assert "HOME_DIR" in raw
    # Never stores a secret.
    for bad in ("TOKEN", "PASSWORD", "API_KEY", "SECRET"):
        assert bad not in raw


@pytest.mark.parametrize(
    "script",
    ["install-gemini.ps1", "install-codex.ps1"],
)
def test_windows_installer_exists_and_scoped(script):
    raw = _read(script)
    assert "@@PROOF_RUN@@" in raw  # rewrites the placeholder
    assert not _PIPE_TO_SHELL.search(raw)
    assert Path(ROOT / script).is_file()
