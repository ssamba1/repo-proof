import json

from proof.scripts.models import Lang, Outcome, ProjectKind, VerifyReport
from proof.scripts.report import apply_edits, to_json, to_markdown


def _report(outcome=Outcome.FIXED):
    rep = VerifyReport(repo="r", lang=Lang.PYTHON, kind=ProjectKind.CLI, outcome=outcome)
    rep.proposed_edits.append(("python man.py", "python main.py"))
    rep.notes.append("corrected line 9")
    return rep


def test_markdown_mentions_outcome():
    md = to_markdown(_report())
    assert "fixed" in md
    assert "Proposed README edit" in md
    assert "python main.py" in md


def test_json_is_valid_and_flags_trustworthy():
    payload = json.loads(to_json(_report(Outcome.VERIFIED)))
    assert payload["outcome"] == "verified"
    assert payload["trustworthy"] is True
    assert payload["exit_code"] == 0


def test_json_untrustworthy_for_real_bug():
    payload = json.loads(to_json(_report(Outcome.REAL_CODE_BUG)))
    assert payload["trustworthy"] is False
    assert payload["exit_code"] == 2


def test_apply_edits_rewrites_readme(tmp_path):
    (tmp_path / "README.md").write_text("Run:\n\n```bash\npython man.py\n```\n", encoding="utf-8")
    changed = apply_edits(tmp_path, _report())
    assert changed == 1
    assert "python main.py" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_apply_edits_noop_without_edits(tmp_path):
    (tmp_path / "README.md").write_text("nothing", encoding="utf-8")
    rep = VerifyReport(repo="r", lang=Lang.PYTHON, kind=ProjectKind.CLI, outcome=Outcome.VERIFIED)
    assert apply_edits(tmp_path, rep) == 0
