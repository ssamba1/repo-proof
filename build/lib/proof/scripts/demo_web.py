"""Capture a real screenshot of a running web app.

Auto-booting an arbitrary web project (port discovery, framework detection, readiness
polling) is unreliable, so v1 takes the honest path: the caller supplies a URL of an
already-running app via `--web URL`. If Playwright is unavailable we skip with a clear
reason rather than pretend.
"""

from __future__ import annotations

from pathlib import Path

from .models import DemoResult


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def capture(url: str, out_dir: Path, timeout_ms: int = 15000) -> DemoResult:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not url:
        return DemoResult("none", None, False, "none", "No --web URL provided.")
    if not playwright_available():
        return DemoResult(
            "none",
            None,
            False,
            "none",
            "Playwright is not installed (pip install 'repo-proof[web]'); skipped.",
        )
    png = out_dir / "proof-demo.png"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            page.screenshot(path=str(png), full_page=True)
            browser.close()
    except Exception as exc:  # noqa: BLE001 — surface any capture failure as a skip, never crash
        return DemoResult("none", None, False, "playwright", f"Capture failed: {exc}")
    return DemoResult("png", str(png), True, "playwright")
