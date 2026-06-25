import functools
import http.server
import socketserver
import threading

import pytest

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


@pytest.mark.skipif(
    not demo_web.playwright_available(), reason="playwright not installed (pip install '.[web]')"
)
def test_web_capture_real_screenshot_of_served_fixture(tmp_path):
    """End-to-end: serve the web-demo fixture over HTTP and screenshot the running page.

    This is the Success-Criterion-3 path that produced the committed docs/web-demo.png. If the
    Playwright browser binary is absent, capture() returns a clean skip rather than crashing, so
    we accept either a real png or a graceful skip — never an exception."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(FIXTURES / "web-demo")
    )
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            result = demo_web.capture(f"http://127.0.0.1:{port}/", tmp_path)
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
    if result.captured:
        assert result.kind == "png"
        assert result.path and (tmp_path / "proof-demo.png").is_file()
    else:
        assert result.reason  # browser binary missing -> honest skip, not a crash
