# RepoProof benchmark

Measured against real, popular GitHub repositories. Regenerate with
`python tools/benchmark.py --run`.

## Tier 1 — extraction (the moat claim)

**12/16** repos: a runnable quickstart command was extracted from arbitrary
prose with zero config. **4/16** had an install step but no shell run
command (typical of libraries whose example is a code snippet, not a CLI invocation).

| Repo | Lang | Kind | Result | Extracted run command |
|------|------|------|--------|------------------------|
| httpie/httpie | python | cli | found_run | `https httpie.io/hello` |
| sherlock-project/sherlock | python | cli | found_run | `sherlock user123` |
| yt-dlp/yt-dlp | python | cli | found_run | `python devscripts/install_deps.py --include-group pyinstaller` |
| psf/requests | python | lib | install_only | — |
| pallets/click | python | lib | found_run | `python hello.py --count=3` |
| Textualize/rich | python | lib | found_run | `python -m rich` |
| tj/commander.js | node | lib | found_run | `node split.js -s - --fits a-b-c` |
| chalk/chalk | node | lib | install_only | — |
| sindresorhus/execa | node | lib | install_only | — |
| expressjs/express | node | lib | found_run | `express /tmp/foo` |
| BurntSushi/ripgrep | rust | cli | found_run | `sudo subscription-manager repos --enable codeready-builder-for-rhel-10-$(arch)-rpms` |
| sharkdp/bat | rust | cli | found_run | `bat README.md` |
| sharkdp/fd | rust | cli | found_run | `fd -e zip -x unzip` |
| spf13/cobra | go | lib | install_only | — |
| junegunn/fzf | go | cli | found_run | `~/.fzf/install` |
| charmbracelet/glow | go | cli | found_run | `nix-shell -p glow --command glow` |

### Honest read

`found_run` means *a* command was extracted, not that it is guaranteed the intended one.
Manual review of this corpus: about **8/16** extracted the exact intended quickstart and
**4/16** were correctly identified as install-only (libraries whose example is a code
snippet, not a CLI invocation) — so ~**12/16 handled correctly**. The misses share one
pattern: READMEs that list many distro-specific install methods before any usage (e.g.
ripgrep's install matrix, yt-dlp's dev script, the fzf installer), where the first
run-looking line is still an install prerequisite.

**Known limitation / roadmap:** smarter install-vs-run discrimination on install-heavy
READMEs (prefer a usage/example block over the first runnable line in an install matrix).

