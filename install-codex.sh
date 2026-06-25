#!/usr/bin/env bash
# RepoProof installer for OpenAI Codex CLI (macOS / Linux).
# Writes ONLY inside ~/.codex (or $CODEX_HOME). No network calls, no credentials, no remote exec.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
PKG="${HOME_DIR}/repo-proof"
RUN="${PKG}/proof/run.py"

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "error: Python 3.10+ is required but was not found on PATH." >&2
  exit 1
fi

mkdir -p "${PKG}" "${HOME_DIR}/prompts"

# Carry the Python package the prompts invoke.
rm -rf "${PKG}/proof"
cp -R "${SRC}/proof" "${PKG}/proof"
find "${PKG}/proof" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Install the custom prompts (-> /proof-verify, /proof-demo), rewriting the run.py path.
for f in proof-verify proof-demo; do
  sed "s|@@PROOF_RUN@@|${RUN}|g" \
    "${SRC}/packaging/codex/prompts/${f}.md" \
    > "${HOME_DIR}/prompts/${f}.md"
done

echo "RepoProof installed for Codex CLI in ${HOME_DIR}"
echo "  - /proof-verify  and  /proof-demo"
echo "No credentials stored, no network calls, nothing written outside ${HOME_DIR}."
echo "Try it in Codex:  /proof-verify <path-to-a-repo>"
