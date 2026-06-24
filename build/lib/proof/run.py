"""Path-independent launcher for the installed skill.

After `install.sh`, the `proof` package lives at ~/.claude/skills/proof. Agents invoke this
file by absolute path from inside whatever repo they are verifying; it puts the package's
parent on sys.path so `python <...>/proof/run.py verify <repo>` works from any directory.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from proof.scripts.cli import main  # noqa: E402 — must follow the sys.path bootstrap above

if __name__ == "__main__":
    raise SystemExit(main())
