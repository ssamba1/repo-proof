from conftest import FIXTURES
from proof.scripts import demo_cli, demo_web


def test_build_tape_is_well_formed():
    tape = demo_cli.build_tape("python main.py", "out.gif")
    assert 'Output "out.gif"' in tape
    assert "Type 'python main.py'" in tape
    assert "Enter" in tape


def test_cli_capture_text_fallback_is_real(tmp_path):
    # No vhs in this environment -> text fallback, which must contain the program's real output.
    result = demo_cli.capture(FIXTURES / "py-working", tmp_path)
    assert result.captured
    assert result.kind in ("gif", "text")
    if result.kind == "text":
        assert result.tool == "text-fallback"
        body = (tmp_path / "proof-demo.md").read_text(encoding="utf-8")
        assert "Hello from py-working" in body


def test_cli_capture_no_runnable_example(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Title\n\nNo commands.\n", encoding="utf-8")
    result = demo_cli.capture(repo, tmp_path / "out")
    assert not result.captured
    assert result.tool == "none"


def test_web_capture_requires_url(tmp_path):
    result = demo_web.capture("", tmp_path)
    assert not result.captured
    assert "No --web URL" in result.reason


def test_web_capture_skips_without_playwright(tmp_path, monkeypatch):
    monkeypatch.setattr(demo_web, "playwright_available", lambda: False)
    result = demo_web.capture("http://localhost:3000", tmp_path)
    assert not result.captured
    assert "Playwright" in result.reason
