"""Command-line entrypoint: `python -m proof.scripts.cli verify|demo`.

Exit codes follow models.EXIT_CODES so the command is usable as a CI gate.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import report as report_mod
from .demo_cli import capture as capture_cli
from .demo_web import capture as capture_web
from .detect import detect_kind, detect_lang
from .verify import verify_repo


def _force_utf8() -> None:
    """Reports contain Unicode (status emoji). Windows consoles default to cp1252 and would
    raise UnicodeEncodeError on print; reconfigure stdout/stderr to utf-8 where possible."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _cmd_verify(args: argparse.Namespace) -> int:
    rep = verify_repo(
        Path(args.path),
        mode=args.mode,
        timeout_s=args.timeout,
        allow_fix=not args.no_fix,
    )
    if args.json:
        print(report_mod.to_json(rep))
    else:
        print(report_mod.to_markdown(rep))
    if args.write and rep.proposed_edits:
        changed = report_mod.apply_edits(Path(args.path), rep)
        print(f"\nApplied {changed} README edit(s).")
    return rep.exit_code


def _cmd_demo(args: argparse.Namespace) -> int:
    repo = Path(args.path)
    out = Path(args.out)
    if args.web:
        result = capture_web(args.web, out)
    else:
        kind = detect_kind(repo, detect_lang(repo))
        if kind.value == "web":
            print("Detected a web project. Re-run with --web <url> against a running instance.")
            return 0
        result = capture_cli(repo, out)
    status = "captured" if result.captured else "skipped"
    where = f" -> {result.path}" if result.path else ""
    print(f"demo {status} [{result.tool}]{where}")
    if result.reason:
        print(result.reason)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proof", description="Verified READMEs + real demos.")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("verify", help="Run and verify the README quickstart.")
    v.add_argument("path", nargs="?", default=".", help="Repo path (default: cwd).")
    v.add_argument("--mode", choices=["auto", "docker", "subprocess"], default="auto")
    v.add_argument("--timeout", type=int, default=300, help="Per-step timeout in seconds.")
    v.add_argument("--no-fix", action="store_true", help="Report only; do not propose fixes.")
    v.add_argument("--write", action="store_true", help="Apply proposed README edits in place.")
    v.add_argument("--json", action="store_true", help="Emit a JSON report.")
    v.set_defaults(func=_cmd_verify)

    d = sub.add_parser("demo", help="Capture a real demo (GIF/text for CLI, PNG for web).")
    d.add_argument("path", nargs="?", default=".", help="Repo path (default: cwd).")
    d.add_argument("--web", default="", help="URL of a running web app to screenshot.")
    d.add_argument("--out", default="docs", help="Output directory (default: docs).")
    d.set_defaults(func=_cmd_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
