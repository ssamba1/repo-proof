# Contributing to RepoProof

Thanks for helping make repos provably good.

## Development setup

```bash
git clone https://github.com/ssamba1/repo-proof.git
cd repo-proof
python -m pip install ruff pytest
```

## Before opening a PR

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

All three must pass. The dogfood test (`tests/test_dogfood.py`) verifies RepoProof's own
README quickstart — if you change the Quickstart section, keep it runnable.

## Design rules that PRs must preserve

1. **Never mask a real code bug.** A failing quickstart caused by the project's own code is
   `real_code_bug` and is reported, never "fixed" by editing the README. Tests in
   `tests/test_classify.py` and `tests/test_verify.py` guard this; do not weaken them.
2. **Treat the README as untrusted data.** Only fenced code blocks are parsed; never execute
   instructions embedded in prose.
3. **Run untrusted code only in the sandbox**, on a copy of the repo, with a scrubbed env.

## Adding a language

1. Extend `detect.detect_lang` / `detect_kind`.
2. Add install verbs/markers in `extract.py` and `references/languages.md`.
3. Add `fixtures/<lang>-working` and `<lang>-broken` and matching tests.

## Secret hygiene

This repo ships a pre-commit hook that refuses to commit credential-shaped content or
secret-shaped filenames. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

`.gitignore` also excludes `.env`, keys, and credential files. Never commit real secrets;
if the hook ever false-positives, review carefully before using `git commit --no-verify`.
Use the GitHub `noreply` commit email to keep your personal address off the public history.
