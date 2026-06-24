import pytest

from conftest import FIXTURES, have
from proof.scripts import sandbox
from proof.scripts.extract import extract_quickstart
from proof.scripts.models import Command, StepKind


def test_scrubbed_env_excludes_secrets(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "supersecret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "nope")
    monkeypatch.setenv("OPENAI_API_KEY", "nope")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = sandbox._scrubbed_env()
    assert "GH_TOKEN" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert "PATH" in env


def test_docker_argv_is_hardened():
    argv = sandbox._docker_argv("python:3.12-slim", "/tmp/work", ["python", "main.py"])
    joined = " ".join(argv)
    assert "--rm" in argv
    assert "--network" not in argv or "none" in argv  # network not opened by default flags
    for flag in ("--cap-drop", "--pids-limit", "--memory", "--cpus", "no-new-privileges"):
        assert flag in joined
    assert argv[-2:] == ["python", "main.py"]


def test_resolve_mode_auto_without_docker(monkeypatch):
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    assert sandbox.resolve_mode("auto") == "subprocess"


def test_run_quickstart_executes_and_cleans(tmp_path, monkeypatch):
    captured = {}
    real_mkdtemp = sandbox.tempfile.mkdtemp

    def spy(*a, **k):
        path = real_mkdtemp(*a, **k)
        captured["path"] = path
        return path

    monkeypatch.setattr(sandbox.tempfile, "mkdtemp", spy)
    cmds = extract_quickstart((FIXTURES / "py-working" / "README.md").read_text(encoding="utf-8"))
    results = sandbox.run_quickstart(
        cmds, FIXTURES / "py-working", lang="python", mode="subprocess"
    )
    assert results[0].ok
    assert "Hello from py-working" in results[0].stdout
    # The temp sandbox is torn down afterward.
    import os

    assert not os.path.exists(captured["path"])


def test_run_quickstart_does_not_pollute_source():
    src = FIXTURES / "py-working"
    before = {p.name for p in src.iterdir()}
    cmd = Command(raw="python main.py", argv=("python", "main.py"), kind=StepKind.RUN)
    sandbox.run_quickstart([cmd], src, lang="python", mode="subprocess")
    after = {p.name for p in src.iterdir()}
    assert before == after


@pytest.mark.skipif(not have("python"), reason="python required")
def test_missing_binary_is_not_a_crash(tmp_path):
    cmd = Command(
        raw="definitely-not-a-real-bin", argv=("definitely-not-a-real-bin",), kind=StepKind.RUN
    )
    results = sandbox.run_quickstart([cmd], FIXTURES / "py-working", mode="subprocess")
    assert results[0].exit_code != 0
    assert not results[0].ok
