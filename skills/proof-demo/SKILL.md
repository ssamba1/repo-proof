---
name: proof-demo
description: >-
  Capture a real demo of a project running — a terminal GIF for a CLI (via vhs) or a screenshot
  for a web app (via Playwright), with a real text-transcript fallback. Never fabricates or
  AI-generates the image. Use when asked to make a demo, record the CLI, screenshot the app, or
  run "/proof demo".
---

# proof-demo

Capture a real artifact of the project working and embed it in the README.

## Steps

1. For a CLI project: `python "$HOME/.claude/skills/proof/run.py" demo <repo-path> --out docs`
   - Uses `vhs` for a GIF when installed; otherwise records a real text transcript of the
     program's actual output. It never invents output.
2. For a web project: start the app, then
   `python "$HOME/.claude/skills/proof/run.py" demo <repo-path> --web http://localhost:<port> --out docs`
   - Requires Playwright (`pip install 'repo-proof[web]'`). Skips with a clear message if absent.
3. Report what was captured (`captured`, `tool`, `path`) and offer to embed it at the top of
   the README.

## Do not

- Do not generate or download a banner/avatar image and present it as a demo.
- Do not claim a GIF exists when only a text transcript was captured.
