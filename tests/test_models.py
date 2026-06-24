from proof.scripts.models import (
    EXIT_CODES,
    GOOD_OUTCOMES,
    Command,
    Outcome,
    RunResult,
    StepKind,
)


def test_every_outcome_has_an_exit_code():
    for outcome in Outcome:
        assert outcome in EXIT_CODES


def test_good_outcomes_are_zero_exit():
    assert frozenset({Outcome.VERIFIED, Outcome.FIXED}) == GOOD_OUTCOMES
    for o in GOOD_OUTCOMES:
        assert EXIT_CODES[o] == 0


def test_failure_outcomes_are_nonzero():
    for o in (Outcome.UNFIXABLE_DOC_ERROR, Outcome.REAL_CODE_BUG, Outcome.EXTRACTION_FAILED):
        assert EXIT_CODES[o] != 0


def test_runresult_ok():
    cmd = Command(raw="python main.py", argv=("python", "main.py"), kind=StepKind.RUN)
    ok = RunResult(cmd, 0, "", "", False, 0.1, "subprocess")
    bad = RunResult(cmd, 1, "", "boom", False, 0.1, "subprocess")
    timed = RunResult(cmd, 124, "", "", True, 0.1, "subprocess")
    assert ok.ok
    assert not bad.ok
    assert not timed.ok
