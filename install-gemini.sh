#!/usr/bin/env bash
# RepoProof installer for Gemini CLI (macOS / Linux).
# Writes ONLY inside ~/.gemini (or $GEMINI_HOME). No network calls, no credentials, no remote exec.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${GEMINI_HOME:-${HOME}/.gemini}"
PKG="${HOME_DIR}/repo-proof"
RUN="${PKG}/proof/run.py"

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "error: Python 3.10+ is required but was not found on PATH." >&2
  exit 1
fi

mkdir -p "${PKG}" "${HOME_DIR}/commands/proof"

# Carry the Python package the commands invoke.
rm -rf "${PKG}/proof"
cp -R "${SRC}/proof" "${PKG}/proof"
find "${PKG}/proof" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Install the custom commands, rewriting the run.py path placeholder.
for f in verify demo; do
  sed "s|@@PROOF_RUN@@|${RUN}|g" \
    "${SRC}/packaging/gemini/commands/proof/${f}.toml" \
    > "${HOME_DIR}/commands/proof/${f}.toml"
done

echo "RepoProof installed for Gemini CLI in ${HOME_DIR}"
echo "  - /proof:verify  and  /proof:demo"
echo "No credentials stored, no network calls, nothing written outside ${HOME_DIR}."
echo "Try it in Gemini CLI:  /proof:verify <path-to-a-repo>"
