import json

import pytest

from conftest import FIXTURES, have
from proof import run as launcher
from proof.scripts.cli import build_parser, main


def test_parser_has_verify_and_demo():
    parser = build_parser()
    ns = parser.parse_args(["verify", "somepath", "--json"])
    assert ns.command == "verify"
    assert ns.json is True
    ns2 = parser.parse_args(["demo", "p", "--web", "http://x"])
    assert ns2.command == "demo"
    assert ns2.web == "http://x"


def test_verify_cli_exit_zero_and_json(capsys):
    code = main(["verify", str(FIXTURES / "py-working"), "--mode", "subprocess", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "verified"
    assert payload["trustworthy"] is True


def test_verify_cli_fixed_reports_diff(capsys):
    code = main(["verify", str(FIXTURES / "py-broken"), "--mode", "subprocess"])
    out = capsys.readouterr().out
    assert code == 0
    assert "python main.py" in out


@pytest.mark.skipif(not have("cargo"), reason="cargo not installed")
def test_verify_cli_real_bug_nonzero_exit(capsys):
    code = main(["verify", str(FIXTURES / "rust-broken"), "--mode", "subprocess", "--json"])
    capsys.readouterr()
    assert code == 2  # real_code_bug


def test_demo_cli_runs(capsys, tmp_path):
    code = main(["demo", str(FIXTURES / "py-working"), "--out", str(tmp_path)])
    assert code == 0
    assert "demo captured" in capsys.readouterr().out


def test_launcher_exposes_main():
    assert callable(launcher.main)
