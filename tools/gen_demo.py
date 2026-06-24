"""Generate docs/demo.gif from REAL RepoProof output.

This is intentionally reproducible: it runs `verify` on a bundled fixture, reads the actual
result (outcome, the corrected command, the verified re-run), and renders that — so the demo in
the README is genuinely the tool's own output, not a staged mockup. Run with:

    python tools/gen_demo.py
"""

from __future__ import annotations

import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from proof.scripts.models import Outcome  # noqa: E402
from proof.scripts.verify import verify_repo  # noqa: E402

# Colors (GitHub-dark palette).
BG = (13, 17, 23)
BAR = (22, 27, 34)
FG = (201, 209, 217)
DIM = (139, 148, 158)
BLUE = (88, 166, 255)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
YELLOW = (210, 153, 34)

FONT_PATH = "C:/Windows/Fonts/CascadiaCode.ttf"
FALLBACK_FONT = "C:/Windows/Fonts/consola.ttf"
SIZE = 20
LINE_H = 30
PAD = 22
BAR_H = 40
W = 860


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (FONT_PATH, FALLBACK_FONT):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_lines() -> list[list[tuple[str, tuple[int, int, int]]]]:
    """Run the real tool and turn its result into colored display segments."""
    rep = verify_repo(ROOT / "fixtures" / "py-broken", mode="subprocess")
    assert rep.outcome is Outcome.FIXED, f"expected FIXED, got {rep.outcome}"
    old, new = rep.proposed_edits[0]
    last_ok = rep.steps[-1].ok

    lines: list[list[tuple[str, tuple[int, int, int]]]] = [
        [("", FG)],  # blank under the typed command (filled at render time)
        [],
        [("  run   ", DIM), (old, FG), ("        failed", RED)],
        [("  fix   ", YELLOW), (f"{old}  ->  {new}", FG)],
        [("  run   ", DIM), (new, FG), ("        ok" if last_ok else "  ?", GREEN)],
        [],
        [("  RESULT  ", DIM), ("fixed", GREEN), (" - README corrected & re-verified", FG)],
    ]
    return lines


def render() -> None:
    mono = _font(SIZE)
    bold = _font(SIZE)
    command = "proof verify ./my-project"
    body = build_lines()
    height = BAR_H + PAD * 2 + LINE_H * (len(body) + 1)

    def base() -> Image.Image:
        img = Image.new("RGB", (W, height), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, BAR_H], fill=BAR)
        for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
            d.ellipse([PAD + i * 26, 14, PAD + i * 26 + 12, 26], fill=c)
        d.text((W / 2, BAR_H / 2), "proof — RepoProof", font=mono, fill=DIM, anchor="mm")
        return img

    def draw_prompt(d: ImageDraw.ImageDraw, typed: str, cursor: bool) -> None:
        y = BAR_H + PAD
        d.text((PAD, y), "$ ", font=bold, fill=BLUE)
        x = PAD + d.textlength("$ ", font=bold)
        d.text((x, y), typed, font=mono, fill=FG)
        if cursor:
            cx = x + d.textlength(typed, font=mono)
            d.rectangle([cx, y + 3, cx + 10, y + SIZE + 4], fill=FG)

    def draw_body(d: ImageDraw.ImageDraw, n: int) -> None:
        for li, segs in enumerate(body[:n]):
            y = BAR_H + PAD + LINE_H * (li + 1)
            x = PAD
            for text, color in segs:
                d.text((x, y), text, font=mono, fill=color)
                x += d.textlength(text, font=mono)

    frames: list[Image.Image] = []
    durations: list[int] = []

    # Phase 1: type the command.
    for i in range(len(command) + 1):
        img = base()
        draw_prompt(ImageDraw.Draw(img), command[:i], cursor=True)
        frames.append(img)
        durations.append(55)
    # small hold after typing
    frames.append(frames[-1].copy())
    durations.append(500)

    # Phase 2: reveal output lines one at a time.
    for n in range(1, len(body) + 1):
        img = base()
        d = ImageDraw.Draw(img)
        draw_prompt(d, command, cursor=False)
        draw_body(d, n)
        frames.append(img)
        durations.append(620)

    # Final hold, then loop.
    frames.append(frames[-1].copy())
    durations.append(2400)

    out = ROOT / "docs" / "demo.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    palette_frames = [f.convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]
    palette_frames[0].save(
        out,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"wrote {out} ({out.stat().st_size // 1024} KB, {len(frames)} frames)")


if __name__ == "__main__":
    render()
