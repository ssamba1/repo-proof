import pytest

from conftest import FIXTURES, have
from proof.scripts.models import Outcome
from proof.scripts.verify import verify_repo


def test_py_working_verified():
    rep = verify_repo(FIXTURES / "py-working", mode="subprocess")
    assert rep.outcome is Outcome.VERIFIED
    assert rep.steps and rep.steps[-1].ok


def test_py_broken_is_fixed():
    rep = verify_repo(FIXTURES / "py-broken", mode="subprocess")
    assert rep.outcome is Outcome.FIXED
    assert rep.proposed_edits == [("python man.py", "python main.py")]
    assert rep.steps[-1].ok


@pytest.mark.skipif(not have("node"), reason="node not installed")
def test_node_working_verified():
    rep = verify_repo(FIXTURES / "node-working", mode="subprocess")
    assert rep.outcome is Outcome.VERIFIED


@pytest.mark.skipif(not have("node"), reason="node not installed")
def test_node_broken_is_fixed():
    rep = verify_repo(FIXTURES / "node-broken", mode="subprocess")
    assert rep.outcome is Outcome.FIXED
    assert rep.proposed_edits == [("node indx.js", "node index.js")]


@pytest.mark.skipif(not have("cargo"), reason="cargo not installed")
def test_rust_working_verified():
    rep = verify_repo(FIXTURES / "rust-working", mode="subprocess", timeout_s=600)
    assert rep.outcome is Outcome.VERIFIED


@pytest.mark.skipif(not have("cargo"), reason="cargo not installed")
def test_rust_broken_is_real_code_bug_not_fixed():
    # Integrity: the README command is correct; the code does not compile. We must report
    # a real bug and must NOT invent a README edit to hide it.
    rep = verify_repo(FIXTURES / "rust-broken", mode="subprocess", timeout_s=600)
    assert rep.outcome is Outcome.REAL_CODE_BUG
    assert rep.proposed_edits == []


@pytest.mark.skipif(not have("ruby"), reason="ruby not installed")
def test_ruby_working_verified():
    rep = verify_repo(FIXTURES / "ruby-working", mode="subprocess")
    assert rep.outcome is Outcome.VERIFIED


@pytest.mark.skipif(not have("ruby"), reason="ruby not installed")
def test_ruby_broken_is_fixed():
    rep = verify_repo(FIXTURES / "ruby-broken", mode="subprocess")
    assert rep.outcome is Outcome.FIXED
    assert rep.proposed_edits == [("ruby man.rb", "ruby main.rb")]


def test_needs_input(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "## Quickstart\n\n```bash\npython main.py --key <your-key>\n```\n", encoding="utf-8"
    )
    rep = verify_repo(tmp_path, mode="subprocess")
    assert rep.outcome is Outcome.NEEDS_INPUT


def test_extraction_failed(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Title\n\nProse only, no commands.\n", encoding="utf-8")
    rep = verify_repo(tmp_path, mode="subprocess")
    assert rep.outcome is Outcome.EXTRACTION_FAILED


def test_unknown_language(tmp_path):
    (tmp_path / "README.md").write_text(
        "## Quickstart\n\n```bash\necho hi\n```\n", encoding="utf-8"
    )
    rep = verify_repo(tmp_path, mode="subprocess")
    assert rep.outcome is Outcome.SANDBOX_UNAVAILABLE
