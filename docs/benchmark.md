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
| yt-dlp/yt-dlp | python | cli | found_run | `yt-dlp --print filename -o "test video.%(ext)s" BaW_jenozKc` |
| psf/requests | python | lib | install_only | — |
| pallets/click | python | lib | found_run | `python hello.py --count=3` |
| Textualize/rich | python | lib | found_run | `python -m rich.spinner` |
| tj/commander.js | node | lib | found_run | `node split.js -s - --fits a-b-c` |
| chalk/chalk | node | lib | install_only | — |
| sindresorhus/execa | node | lib | install_only | — |
| expressjs/express | node | lib | found_run | `express /tmp/foo` |
| BurntSushi/ripgrep | rust | cli | found_run | `cargo test --all` |
| sharkdp/bat | rust | cli | found_run | `bat README.md` |
| sharkdp/fd | rust | cli | found_run | `fd -e zip -x unzip` |
| spf13/cobra | go | lib | install_only | — |
| junegunn/fzf | go | cli | found_run | `eval "$(fzf --bash)"` |
| charmbracelet/glow | go | cli | found_run | `nix-shell -p glow --command glow` |

### Honest read

`found_run` means *a* command was extracted, not that it is guaranteed the intended one.
Manual review of this corpus: about **9/16** extracted the exact intended quickstart and
**4/16** were correctly identified as install-only (libraries whose example is a code
snippet, not a CLI invocation) — so ~**13/16 handled correctly**, up from ~6/16
before the extractor was hardened against this corpus. The remaining miss is a README
that buries usage beneath a long distro-specific install matrix (e.g. ripgrep).

**Known limitation / roadmap:** install-method-heavy READMEs whose usage examples are not
in a fenced shell block near a usage heading.

