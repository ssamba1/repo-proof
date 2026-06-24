#!/usr/bin/env bash
# RepoProof installer (macOS / Linux).
# Writes ONLY inside ~/.claude/skills. No network calls, no credentials, no curl|bash.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${HOME}/.claude/skills"

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "error: Python 3.10+ is required but was not found on PATH." >&2
  exit 1
fi

mkdir -p "${DEST}"

# Orchestrator skill (carries the Python package the sub-skills invoke).
rm -rf "${DEST}/proof"
cp -R "${SRC}/proof" "${DEST}/proof"

# Sub-skills.
for skill in proof-verify proof-demo; do
  rm -rf "${DEST}/${skill}"
  cp -R "${SRC}/skills/${skill}" "${DEST}/${skill}"
done

# Drop any compiled caches that may have come along.
find "${DEST}/proof" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

echo "RepoProof installed to ${DEST}"
echo "  - proof, proof-verify, proof-demo"
echo "No credentials stored, no network calls, nothing written outside ~/.claude."
echo "Try it:  python \"${DEST}/proof/run.py\" verify <path-to-a-repo>"
