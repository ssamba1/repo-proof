from proof.scripts.classify import classify_failure
from proof.scripts.models import Command, Outcome, RunResult, StepKind


def _result(stdout="", stderr="", exit_code=1, timed_out=False, raw="python main.py", argv=None):
    cmd = Command(raw=raw, argv=tuple(argv or raw.split()), kind=StepKind.RUN)
    return RunResult(cmd, exit_code, stdout, stderr, timed_out, 0.1, "subprocess")


def test_timeout(tmp_path):
    d = classify_failure(_result(timed_out=True, exit_code=124), tmp_path)
    assert d.outcome is Outcome.TIMEOUT


def test_toolchain_missing(tmp_path):
    d = classify_failure(_result(stderr="cargo: command not found"), tmp_path)
    assert d.outcome is Outcome.SANDBOX_UNAVAILABLE


def test_needs_services(tmp_path):
    d = classify_failure(_result(stderr="Error: connection refused (ECONNREFUSED)"), tmp_path)
    assert d.outcome is Outcome.NEEDS_SERVICES


def test_real_code_bug_rust(tmp_path):
    d = classify_failure(_result(stderr="error[E0308]: mismatched types"), tmp_path)
    assert d.outcome is Outcome.REAL_CODE_BUG
    assert d.suggested_fix is None


def test_real_code_bug_python_traceback(tmp_path):
    err = 'Traceback (most recent call last):\n  File "main.py", line 2\nValueError: nope'
    d = classify_failure(_result(stderr=err), tmp_path)
    assert d.outcome is Outcome.REAL_CODE_BUG


def test_doc_typo_is_fixed(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')", encoding="utf-8")
    res = _result(
        stderr="python: can't open file 'man.py': [Errno 2] No such file or directory",
        raw="python man.py",
        argv=["python", "man.py"],
    )
    d = classify_failure(res, tmp_path)
    assert d.outcome is Outcome.FIXED
    assert d.suggested_fix is not None
    assert d.suggested_fix.argv == ("python", "main.py")


def test_integrity_code_bug_wins_over_path_lookalike(tmp_path):
    # A failure that mentions a missing-ish file BUT clearly shows a repo code crash must
    # be classified as a real bug, never silently "fixed".
    (tmp_path / "main.py").write_text("x", encoding="utf-8")
    err = 'Traceback (most recent call last):\n  File "main.py", line 1\nNameError: x'
    d = classify_failure(_result(stderr=err, raw="python main.py"), tmp_path)
    assert d.outcome is Outcome.REAL_CODE_BUG
    assert d.suggested_fix is None


def test_unfixable_when_no_signal(tmp_path):
    d = classify_failure(_result(stderr="exited with status 1"), tmp_path)
    assert d.outcome is Outcome.UNFIXABLE_DOC_ERROR
